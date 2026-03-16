"""Markdown source discovery for Docsmith documents."""

from __future__ import annotations

from pathlib import Path

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.paths import resolve_document_path


def _validate_markdown_file(path: Path) -> Path:
    """Validate that a discovered input exists and is a Markdown file."""
    if not path.exists():
        raise FileNotFoundError(f"Markdown source not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Markdown source is not a file: {path}")
    if path.suffix.lower() != ".md":
        raise ValueError(f"Markdown source must use a .md extension: {path}")
    return path


def discover_markdown_files(
    document_root: Path,
    config: DocsmithConfig | None = None,
) -> list[Path]:
    """Resolve ordered Markdown sources for a document.

    If `document.include` is configured, that explicit order is used.
    Otherwise all Markdown files under `document.input_root` are discovered
    recursively and sorted by relative path.
    """
    document_root = document_root.resolve()
    config = config or load_document_config(document_root / "spec.yaml")

    input_root = resolve_document_path(config.document.input_root, document_root)
    if not input_root.exists():
        raise FileNotFoundError(f"Document input root not found: {input_root}")
    if not input_root.is_dir():
        raise NotADirectoryError(f"Document input root is not a directory: {input_root}")

    if config.document.include:
        ordered_files = [
            _validate_markdown_file(resolve_document_path(relative_path, input_root))
            for relative_path in config.document.include
        ]
    else:
        ordered_files = sorted(
            _validate_markdown_file(path)
            for path in input_root.rglob("*.md")
            if path.is_file()
        )

    if not ordered_files:
        raise FileNotFoundError(f"No Markdown files found under: {input_root}")

    return ordered_files
