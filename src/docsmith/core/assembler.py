"""Markdown assembly for Docsmith documents."""

from __future__ import annotations

from pathlib import Path

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.discovery import discover_markdown_files


def assemble_markdown(
    document_root: Path,
    config: DocsmithConfig | None = None,
) -> str:
    """Assemble ordered Markdown sources into one document string."""
    document_root = document_root.resolve()
    config = config or load_document_config(document_root / "spec.yaml")
    markdown_files = discover_markdown_files(document_root, config)

    assembled_parts: list[str] = []
    for markdown_file in markdown_files:
        relative_path = markdown_file.relative_to(document_root)
        content = markdown_file.read_text(encoding="utf-8").strip()
        content = content.replace(
            config.document.appendix_marker,
            "\\appendix\n",
        )
        assembled_parts.append(f"<!-- begin:{relative_path.as_posix()} -->\n{content}")

    return "\n\n".join(assembled_parts) + "\n"
