"""Build fingerprint computation for Docsmith."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from docsmith.config import DocsmithConfig
from docsmith.core.crossrefs import document_has_cross_reference_authoring
from docsmith.core.discovery import discover_markdown_files
from docsmith.core.paths import resolve_document_path
from docsmith.renderer.diagrams import diagram_renderer_code_path
from docsmith.renderer.pandoc import cross_reference_filter_path, table_column_widths_filter_path
from docsmith.templates.registry import validate_template


@dataclass(frozen=True)
class FingerprintInput:
    """A file that contributes to the build fingerprint."""

    label: str
    path: Path
    relative_key: str


def _template_inputs(template: str, document_root: Path) -> list[FingerprintInput]:
    """Return template files that affect rendering."""
    template_root = validate_template(template, document_root)
    files = sorted(
        path
        for path in template_root.rglob("*")
        if path.is_file() and path.name != "README.md"
    )
    return [
        FingerprintInput(
            label="template",
            path=path,
            relative_key=path.relative_to(template_root).as_posix(),
        )
        for path in files
    ]


def collect_fingerprint_inputs(
    document_root: Path,
    config: DocsmithConfig,
) -> list[FingerprintInput]:
    """Collect effective build inputs for fingerprinting."""
    document_root = document_root.resolve()
    inputs = [
        FingerprintInput(
            label="spec",
            path=document_root / "spec.yaml",
            relative_key="spec.yaml",
        )
    ]

    inputs.extend(
        FingerprintInput(
            label="markdown",
            path=path,
            relative_key=path.relative_to(document_root).as_posix(),
        )
        for path in discover_markdown_files(document_root, config)
    )
    inputs.extend(_template_inputs(config.project.template, document_root))

    widths_filter_path = table_column_widths_filter_path()
    inputs.append(
        FingerprintInput(
            label="renderer_filter",
            path=widths_filter_path,
            relative_key="docsmith/renderer/filters/table_column_widths.lua",
        )
    )

    for diagram in config.diagrams:
        diagram_source_path = resolve_document_path(diagram.source, document_root)
        inputs.append(
            FingerprintInput(
                label="diagram_source",
                path=diagram_source_path,
                relative_key=diagram_source_path.relative_to(document_root).as_posix()
                if diagram_source_path.is_relative_to(document_root)
                else diagram_source_path.as_posix(),
            )
        )

    if config.diagrams:
        renderer_code_path = diagram_renderer_code_path()
        inputs.append(
            FingerprintInput(
                label="diagram_renderer",
                path=renderer_code_path,
                relative_key="docsmith/renderer/diagrams.py",
            )
        )

    if document_has_cross_reference_authoring(document_root, config):
        filter_path = cross_reference_filter_path()
        inputs.append(
            FingerprintInput(
                label="renderer_filter",
                path=filter_path,
                relative_key="docsmith/renderer/filters/figure_table_crossrefs.lua",
            )
        )

    if config.citations.bibliography:
        bibliography_path = resolve_document_path(
            config.citations.bibliography,
            document_root,
        )
        inputs.append(
            FingerprintInput(
                label="bibliography",
                path=bibliography_path,
                relative_key=bibliography_path.relative_to(document_root).as_posix()
                if bibliography_path.is_relative_to(document_root)
                else bibliography_path.as_posix(),
            )
        )

    if config.citations.csl:
        csl_path = resolve_document_path(config.citations.csl, document_root)
        inputs.append(
            FingerprintInput(
                label="csl",
                path=csl_path,
                relative_key=csl_path.relative_to(document_root).as_posix()
                if csl_path.is_relative_to(document_root)
                else csl_path.as_posix(),
            )
        )

    return inputs


def compute_build_fingerprint(
    document_root: Path,
    config: DocsmithConfig,
) -> str:
    """Compute a stable fingerprint from effective build inputs."""
    digest = hashlib.sha256()

    for fingerprint_input in collect_fingerprint_inputs(document_root, config):
        digest.update(fingerprint_input.label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(fingerprint_input.relative_key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(fingerprint_input.path.read_bytes())
        digest.update(b"\0")

    return digest.hexdigest()
