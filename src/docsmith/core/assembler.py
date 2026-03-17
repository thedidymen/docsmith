"""Markdown assembly for Docsmith documents."""

from __future__ import annotations

from pathlib import Path

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.discovery import resolve_document_structure


def _normalize_markdown_content(
    content: str,
    config: DocsmithConfig,
    *,
    is_appendix: bool,
) -> str:
    """Normalize assembled Markdown content for rendering."""
    if is_appendix:
        return content.replace(config.document.appendix_marker, "").strip()

    return content.replace(
        config.document.appendix_marker,
        "\\appendix\n",
    ).strip()


def _render_bibliography_block(config: DocsmithConfig) -> str:
    """Render a Pandoc-native bibliography placeholder block."""
    if not config.citations.bibliography:
        raise ValueError(
            "Document bibliography placement requires `citations.bibliography` to be configured."
        )

    title = config.document.bibliography.title.strip()
    heading = f"# {title}\n\n" if title else ""
    return f"{heading}::: {{#refs}}\n:::"


def _render_toc_block(config: DocsmithConfig) -> str:
    """Render a TOC placeholder block for the current PDF-first flow."""
    title = config.document.toc.title.strip()
    heading = f"# {title}\n\n" if title else ""
    return f"{heading}```{{=latex}}\n\\tableofcontents\n```"


def assemble_markdown(
    document_root: Path,
    config: DocsmithConfig | None = None,
) -> str:
    """Assemble ordered Markdown sources into one document string."""
    document_root = document_root.resolve()
    config = config or load_document_config(document_root / "spec.yaml")
    structure = resolve_document_structure(document_root, config)

    assembled_parts: list[str] = []
    for zone in structure.zones:
        if not zone.files:
            if (
                (structure.bibliography is None or structure.bibliography.zone != zone.name)
                and (structure.toc is None or structure.toc.zone != zone.name)
            ):
                continue
        assembled_parts.append(f"<!-- zone:{zone.name} -->")
        if structure.toc is not None and structure.toc.zone == zone.name:
            assembled_parts.append("<!-- toc-begin -->")
            assembled_parts.append(_render_toc_block(config))
        if zone.name == "appendices":
            assembled_parts.append("<!-- appendix-begin -->")
            assembled_parts.append("\\appendix")
        for markdown_file in zone.files:
            relative_path = markdown_file.relative_to(document_root)
            content = _normalize_markdown_content(
                markdown_file.read_text(encoding="utf-8"),
                config,
                is_appendix=zone.name == "appendices",
            )
            assembled_parts.append(f"<!-- begin:{relative_path.as_posix()} -->\n{content}")
        if structure.bibliography is not None and structure.bibliography.zone == zone.name:
            assembled_parts.append("<!-- bibliography-begin -->")
            assembled_parts.append(_render_bibliography_block(config))

    return "\n\n".join(assembled_parts) + "\n"
