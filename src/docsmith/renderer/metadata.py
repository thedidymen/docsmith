"""Runtime metadata preparation for Pandoc."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
) -> dict[str, Any]:
    """Build the runtime metadata passed to Pandoc."""
    metadata: dict[str, Any] = dict(config.metadata)
    metadata["version"] = version
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
    output_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output_path
