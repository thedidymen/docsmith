"""Pandoc PDF rendering for Docsmith."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from docsmith.config import DocsmithConfig, document_has_structural_toc
from docsmith.core.paths import resolve_document_path
from docsmith.renderer.defaults import template_defaults_path
from docsmith.renderer.metadata import metadata_output_path
from docsmith.renderer.preflight import (
    describe_missing_pdf_dependencies,
    validate_pdf_dependencies,
)
from docsmith.templates.registry import validate_template


class PandocRenderError(RuntimeError):
    """Raised when Pandoc rendering fails."""


def _template_root(template: str, document_root: Path) -> Path:
    """Resolve a template directory relative to the document root."""
    return validate_template(template, document_root)


def _resource_path(input_file: Path, document_root: Path) -> str:
    """Build a Pandoc resource path covering generated and source document assets."""
    candidate_paths: list[Path] = []
    for candidate in (input_file.parent.resolve(), document_root.resolve()):
        if candidate not in candidate_paths:
            candidate_paths.append(candidate)
    return os.pathsep.join(str(path) for path in candidate_paths)


def build_pandoc_command(
    input_file: Path,
    output_file: Path,
    *,
    document_root: Path,
    config: DocsmithConfig,
    template_name: str,
    metadata_file: Path | None = None,
) -> list[str]:
    """Build a Pandoc command for PDF output using a document-local template."""
    template_root = _template_root(template_name, document_root)
    defaults_file = template_defaults_path(template_root)
    template_file = template_root / "template.tex"

    if not defaults_file.exists():
        raise FileNotFoundError(f"Template defaults file not found: {defaults_file}")
    if not template_file.exists():
        raise FileNotFoundError(f"Template LaTeX file not found: {template_file}")

    command = [
        "pandoc",
        str(input_file),
        "--defaults",
        str(defaults_file),
        "--resource-path",
        _resource_path(input_file, document_root),
        "--template",
        str(template_file),
        "-o",
        str(output_file),
    ]

    if metadata_file is not None:
        command.extend(["--metadata-file", str(metadata_file)])

    if document_has_structural_toc(config):
        command.extend(["-M", "toc=false"])

    if config.citations.bibliography:
        bibliography_path = resolve_document_path(
            config.citations.bibliography,
            document_root,
        )
        command.extend(["--bibliography", str(bibliography_path)])

    if config.citations.csl:
        csl_path = resolve_document_path(config.citations.csl, document_root)
        command.extend(["--csl", str(csl_path)])

    return command


def render_pdf(
    input_file: Path,
    output_file: Path,
    *,
    config: DocsmithConfig,
    document_root: Path | None = None,
    build_dir: Path | None = None,
    metadata_file: Path | None = None,
) -> Path:
    """Render an assembled Markdown file to PDF with Pandoc."""
    if input_file.suffix.lower() != ".md":
        raise ValueError(f"Input file must be Markdown: {input_file}")
    if output_file.suffix.lower() != ".pdf":
        raise ValueError(f"Output file must be a PDF path: {output_file}")

    if metadata_file is None and build_dir is not None:
        candidate = metadata_output_path(build_dir)
        if candidate.exists():
            metadata_file = candidate

    output_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_document_root = (
        document_root.resolve()
        if document_root is not None
        else input_file.parent.parent if build_dir is None else build_dir.parent
    )
    template_root = _template_root(config.project.template, resolved_document_root)
    missing_dependencies = validate_pdf_dependencies(template_root)
    if missing_dependencies:
        raise PandocRenderError(describe_missing_pdf_dependencies(missing_dependencies))

    command = build_pandoc_command(
        input_file,
        output_file,
        document_root=resolved_document_root,
        config=config,
        template_name=config.project.template,
        metadata_file=metadata_file,
    )

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise PandocRenderError(
            "Could not start the PDF build toolchain. "
            "Install pandoc and the configured PDF engine, and ensure both are on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        message = "Pandoc PDF rendering failed."
        lowered_stderr = stderr.lower()
        if "xelatex not found" in lowered_stderr or "xelatex: not found" in lowered_stderr:
            message = (
                "Pandoc PDF rendering failed because `xelatex` is unavailable. "
                "Install a TeX distribution that provides `xelatex` and ensure it is on PATH."
            )
        elif "pdflatex not found" in lowered_stderr or "pdflatex: not found" in lowered_stderr:
            message = (
                "Pandoc PDF rendering failed because the configured LaTeX engine is unavailable. "
                "Install the required TeX engine and ensure it is on PATH."
            )
        if stderr:
            message = f"{message} {stderr}"
        raise PandocRenderError(message) from exc

    return output_file
