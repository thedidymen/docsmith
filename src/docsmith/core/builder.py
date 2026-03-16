"""Build orchestration for the Docsmith MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.assembler import assemble_markdown
from docsmith.renderer.metadata import write_runtime_metadata
from docsmith.renderer.pandoc import render_pdf
from docsmith.versioning.fingerprint import compute_build_fingerprint
from docsmith.versioning.git import get_git_short_hash
from docsmith.versioning.resolver import (
    BumpLevel,
    VersionResolution,
    resolve_output_path,
    resolve_semantic_version,
)
from docsmith.versioning.state import load_build_state, save_build_state, state_file_path


@dataclass(frozen=True)
class BuildResult:
    """Artifacts produced by a Docsmith build."""

    document_root: Path
    build_dir: Path
    assembled_markdown_path: Path
    metadata_path: Path
    output_path: Path
    version_info: VersionResolution
    state_path: Path


def build_document(
    document_root: Path,
    *,
    bump: BumpLevel | None = None,
    no_bump: bool = False,
) -> BuildResult:
    """Run the first end-to-end MVP build flow for a document directory."""
    document_root = document_root.resolve()
    config: DocsmithConfig = load_document_config(document_root / "spec.yaml")

    build_dir = document_root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    prior_state = load_build_state(build_dir)
    fingerprint = compute_build_fingerprint(document_root, config)
    git_hash = get_git_short_hash(document_root) if config.versioning.include_git_hash else None
    version_info = resolve_semantic_version(
        config,
        fingerprint=fingerprint,
        prior_state=prior_state,
        bump=bump,
        no_bump=no_bump,
        git_hash=git_hash,
    )

    assembled_markdown = assemble_markdown(document_root, config)
    assembled_markdown_path = build_dir / "combined.md"
    assembled_markdown_path.write_text(assembled_markdown, encoding="utf-8")

    metadata_path = write_runtime_metadata(
        build_dir,
        document_root,
        config,
        version=version_info.semantic_version,
        git_hash=version_info.git_hash,
    )
    output_path = resolve_output_path(
        document_root,
        config,
        "pdf",
        version=version_info.semantic_version,
        git_hash=version_info.git_hash,
    )

    render_pdf(
        assembled_markdown_path,
        output_path,
        config=config,
        document_root=document_root,
        build_dir=build_dir,
        metadata_file=metadata_path,
    )
    state_path = save_build_state(
        build_dir,
        current_version=version_info.semantic_version,
        fingerprint=fingerprint,
        git_hash=version_info.git_hash,
    )

    return BuildResult(
        document_root=document_root,
        build_dir=build_dir,
        assembled_markdown_path=assembled_markdown_path,
        metadata_path=metadata_path,
        output_path=output_path,
        version_info=version_info,
        state_path=state_path,
    )
