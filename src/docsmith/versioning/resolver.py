"""Version and output path resolution for Docsmith."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from docsmith.config import DocsmithConfig
from docsmith.core.paths import resolve_document_path
from docsmith.versioning.git import get_git_short_hash
from docsmith.versioning.state import BuildState

BumpLevel = Literal["patch", "minor", "major"]


@dataclass(frozen=True)
class VersionResolution:
    """Resolved build version information."""

    semantic_version: str
    previous_version: str | None
    fingerprint_changed: bool
    bump_applied: BumpLevel | None
    git_hash: str | None


def resolve_version_string(config: DocsmithConfig) -> str:
    """Resolve the configured base version token."""
    if config.versioning.strategy == "timestamp":
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    return config.versioning.initial_version


def bump_semantic_version(version: str, level: BumpLevel) -> str:
    """Bump a semantic version string."""
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Semantic version must use MAJOR.MINOR.PATCH: {version}")

    major, minor, patch = (int(part) for part in parts)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump level: {level}")


def resolve_semantic_version(
    config: DocsmithConfig,
    *,
    fingerprint: str,
    prior_state: BuildState | None,
    bump: BumpLevel | None = None,
    no_bump: bool = False,
    git_hash: str | None = None,
) -> VersionResolution:
    """Resolve the semantic version for a build."""
    previous_version = prior_state.current_version if prior_state is not None else None
    base_version = previous_version or config.versioning.initial_version
    fingerprint_changed = (
        prior_state.last_fingerprint != fingerprint if prior_state is not None else False
    )

    bump_applied: BumpLevel | None = None
    semantic_version = base_version

    if bump is not None:
        semantic_version = bump_semantic_version(base_version, bump)
        bump_applied = bump
    elif not no_bump and fingerprint_changed:
        semantic_version = bump_semantic_version(base_version, "patch")
        bump_applied = "patch"

    return VersionResolution(
        semantic_version=semantic_version,
        previous_version=previous_version,
        fingerprint_changed=fingerprint_changed,
        bump_applied=bump_applied,
        git_hash=git_hash,
    )


def build_output_filename(
    basename: str,
    version: str,
    extension: str,
    git_hash: str | None = None,
    collision_index: int | None = None,
) -> str:
    """Build a versioned output filename."""
    normalized_extension = extension.lstrip(".")
    segments = [f"{basename}_v{version}"]
    if git_hash:
        segments.append(git_hash)
    if collision_index is not None:
        segments.append(f"{collision_index:02d}")
    return f"{'_'.join(segments)}.{normalized_extension}"


def resolve_output_filename(
    document_root: Path,
    config: DocsmithConfig,
    extension: str,
    *,
    version: str,
    git_hash: str | None = None,
    collision_index: int | None = None,
) -> str:
    """Resolve a versioned output filename."""
    effective_git_hash = git_hash
    if effective_git_hash is None and config.versioning.include_git_hash:
        effective_git_hash = get_git_short_hash(document_root)

    return build_output_filename(
        basename=config.output.basename,
        version=version,
        extension=extension,
        git_hash=effective_git_hash,
        collision_index=collision_index,
    )


def resolve_output_path(
    document_root: Path,
    config: DocsmithConfig,
    extension: str,
    *,
    version: str,
    git_hash: str | None = None,
) -> Path:
    """Resolve a non-overwriting output path for a rendered artifact."""
    output_dir = resolve_document_path(config.output.directory, document_root)
    collision_index = None

    while True:
        filename = resolve_output_filename(
            document_root,
            config,
            extension,
            version=version,
            git_hash=git_hash,
            collision_index=collision_index,
        )
        output_path = output_dir / filename
        if not output_path.exists():
            return output_path
        collision_index = 1 if collision_index is None else collision_index + 1
