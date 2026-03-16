"""Document validation for Docsmith."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from docsmith.config import DocsmithConfig, load_document_config
from docsmith.core.discovery import discover_markdown_files
from docsmith.core.paths import resolve_document_path
from docsmith.renderer.preflight import (
    describe_missing_pdf_dependencies,
    required_pdf_dependencies,
    validate_pdf_dependencies,
)
from docsmith.templates.registry import validate_template


@dataclass(frozen=True)
class ValidationCheck:
    """Single validation check result."""

    label: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation report for a document directory."""

    document_root: Path
    checks: list[ValidationCheck]

    @property
    def ok(self) -> bool:
        """Return whether all checks passed."""
        return all(check.ok for check in self.checks)


def _run_check(label: str, validator: Callable[[], str]) -> ValidationCheck:
    """Execute a validation step and capture its outcome."""
    try:
        detail = validator()
    except Exception as exc:
        return ValidationCheck(label=label, ok=False, detail=str(exc))

    return ValidationCheck(label=label, ok=True, detail=detail)


def _validate_spec_loading(document_root: Path) -> tuple[DocsmithConfig, ValidationCheck]:
    """Load the document spec and return both config and check result."""
    config = load_document_config(document_root / "spec.yaml")
    check = ValidationCheck(
        label="spec.yaml loading",
        ok=True,
        detail=f"Loaded {(document_root / 'spec.yaml').resolve()}",
    )
    return config, check


def _validate_input_root(document_root: Path, config: DocsmithConfig) -> str:
    """Validate the configured document input root."""
    input_root = resolve_document_path(config.document.input_root, document_root)
    if not input_root.exists():
        raise FileNotFoundError(f"Document input root not found: {input_root}")
    if not input_root.is_dir():
        raise NotADirectoryError(f"Document input root is not a directory: {input_root}")
    return f"Found {input_root}"


def _validate_markdown_inputs(document_root: Path, config: DocsmithConfig) -> str:
    """Validate included Markdown inputs or discovered Markdown files."""
    markdown_files = discover_markdown_files(document_root, config)
    return f"Resolved {len(markdown_files)} Markdown file(s)"


def _validate_template(document_root: Path, config: DocsmithConfig) -> str:
    """Validate the configured template."""
    template_path = validate_template(config.project.template, document_root)
    return f"Found template at {template_path}"


def _validate_pdf_dependencies(document_root: Path, config: DocsmithConfig) -> str:
    """Validate external dependencies required for PDF rendering."""
    if "pdf" not in config.output.formats:
        return "No PDF build dependencies required"

    template_path = validate_template(config.project.template, document_root)
    missing_dependencies = validate_pdf_dependencies(template_path)
    if missing_dependencies:
        raise RuntimeError(describe_missing_pdf_dependencies(missing_dependencies))

    dependencies = ", ".join(required_pdf_dependencies(template_path))
    return f"Found external PDF build dependencies: {dependencies}"


def _validate_citation_assets(document_root: Path, config: DocsmithConfig) -> str:
    """Validate bibliography and CSL paths when configured."""
    checked_paths: list[str] = []

    if config.citations.bibliography:
        bibliography_path = resolve_document_path(
            config.citations.bibliography,
            document_root,
        )
        if not bibliography_path.exists():
            raise FileNotFoundError(f"Bibliography file not found: {bibliography_path}")
        if not bibliography_path.is_file():
            raise FileNotFoundError(f"Bibliography path is not a file: {bibliography_path}")
        checked_paths.append(str(bibliography_path))

    if config.citations.csl:
        csl_path = resolve_document_path(config.citations.csl, document_root)
        if not csl_path.exists():
            raise FileNotFoundError(f"CSL file not found: {csl_path}")
        if not csl_path.is_file():
            raise FileNotFoundError(f"CSL path is not a file: {csl_path}")
        checked_paths.append(str(csl_path))

    if not checked_paths:
        return "No bibliography or CSL configured"

    return f"Found {len(checked_paths)} citation asset(s)"


def _validate_output_directory(document_root: Path, config: DocsmithConfig) -> str:
    """Validate output directory resolution and creatability."""
    output_dir = resolve_document_path(config.output.directory, document_root)

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_dir}")
    if output_dir.exists():
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {output_dir}")
        return f"Output directory is writable: {output_dir}"

    existing_parent = output_dir.parent
    while not existing_parent.exists() and existing_parent != existing_parent.parent:
        existing_parent = existing_parent.parent

    if not existing_parent.exists():
        raise FileNotFoundError(
            f"Could not resolve a writable parent for output directory: {output_dir}"
        )
    if not existing_parent.is_dir():
        raise NotADirectoryError(
            f"Output directory parent is not a directory: {existing_parent}"
        )
    if not os.access(existing_parent, os.W_OK):
        raise PermissionError(
            f"Cannot create output directory under non-writable parent: {existing_parent}"
        )

    return f"Output directory can be created at {output_dir}"


def validate_document(document_root: Path) -> ValidationReport:
    """Validate a document directory and return a structured report."""
    document_root = document_root.resolve()
    checks: list[ValidationCheck] = []

    try:
        config, spec_check = _validate_spec_loading(document_root)
    except Exception as exc:
        checks.append(
            ValidationCheck(
                label="spec.yaml loading",
                ok=False,
                detail=str(exc),
            )
        )
        return ValidationReport(document_root=document_root, checks=checks)

    checks.append(spec_check)
    checks.append(
        _run_check(
            "document input root existence",
            lambda: _validate_input_root(document_root, config),
        )
    )
    checks.append(
        _run_check(
            "included markdown files existence",
            lambda: _validate_markdown_inputs(document_root, config),
        )
    )
    checks.append(
        _run_check(
            "template existence and required files",
            lambda: _validate_template(document_root, config),
        )
    )
    checks.append(
        _run_check(
            "external PDF build dependencies",
            lambda: _validate_pdf_dependencies(document_root, config),
        )
    )
    checks.append(
        _run_check(
            "bibliography and CSL path existence",
            lambda: _validate_citation_assets(document_root, config),
        )
    )
    checks.append(
        _run_check(
            "output directory resolution/creatability",
            lambda: _validate_output_directory(document_root, config),
        )
    )

    return ValidationReport(document_root=document_root, checks=checks)


def format_validation_report(report: ValidationReport) -> str:
    """Render a human-readable validation report."""
    lines = [f"Validation results for {report.document_root}"]
    for check in report.checks:
        status = "PASS" if check.ok else "FAIL"
        lines.append(f"[{status}] {check.label}: {check.detail}")

    summary = "Validation succeeded." if report.ok else "Validation failed."
    lines.append(summary)
    return "\n".join(lines)
