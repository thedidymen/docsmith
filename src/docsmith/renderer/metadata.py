"""Runtime metadata preparation for Pandoc."""

from __future__ import annotations

from pathlib import Path

from docsmith.config import DocsmithConfig

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in bare environments.
    yaml = None


def metadata_output_path(build_dir: Path) -> Path:
    """Return the expected runtime metadata file path."""
    return build_dir / "runtime-metadata.yaml"


def build_runtime_metadata(
    document_root: Path,
    config: DocsmithConfig,
    *,
    version: str,
    git_hash: str | None = None,
) -> dict[str, str]:
    """Build the runtime metadata passed to Pandoc."""
    metadata: dict[str, str] = {
        "title": config.metadata.title,
        "author": config.metadata.author,
        "version": version,
    }

    if config.metadata.subtitle:
        metadata["subtitle"] = config.metadata.subtitle
    if config.metadata.date:
        metadata["date"] = config.metadata.date
    if git_hash:
        metadata["git_hash"] = git_hash

    return metadata


def write_runtime_metadata(
    build_dir: Path,
    document_root: Path,
    config: DocsmithConfig,
    *,
    version: str,
    git_hash: str | None = None,
) -> Path:
    """Write runtime metadata to the build directory in YAML format."""
    build_dir.mkdir(parents=True, exist_ok=True)
    output_path = metadata_output_path(build_dir)
    metadata = build_runtime_metadata(
        document_root,
        config,
        version=version,
        git_hash=git_hash,
    )

    if yaml is not None:
        output_path.write_text(
            yaml.safe_dump(
                metadata,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return output_path

    lines = []
    for key, value in metadata.items():
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        lines.append(f'{key}: "{escaped_value}"')
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
