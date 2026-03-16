"""Template discovery and validation for document-local template paths."""

from __future__ import annotations

from pathlib import Path

from docsmith.core.paths import resolve_document_path

REQUIRED_TEMPLATE_FILES = ("template.tex", "defaults.yaml")


def templates_root(base_dir: Path | None = None) -> Path:
    """Return the local templates directory for a document or working tree."""
    root = Path.cwd() if base_dir is None else Path(base_dir)
    return (root / "templates").resolve()


def list_templates(base_dir: Path | None = None) -> list[str]:
    """List template directories under a local templates root."""
    root = templates_root(base_dir)
    if not root.exists():
        return []

    return sorted(path.name for path in root.iterdir() if path.is_dir())


def get_template_path(template: str | Path, document_root: Path) -> Path:
    """Resolve a template path relative to a document root."""
    template_path = resolve_document_path(template, document_root)

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}. "
            "Set `project.template` to a valid path relative to the document root."
        )
    if not template_path.is_dir():
        raise NotADirectoryError(f"Template path is not a directory: {template_path}")

    return template_path


def validate_template(template: str | Path, document_root: Path) -> Path:
    """Validate that a template path contains the required files."""
    template_path = get_template_path(template, document_root)
    missing_files = [
        file_name for file_name in REQUIRED_TEMPLATE_FILES if not (template_path / file_name).exists()
    ]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(
            f"Template at '{template_path}' is missing required files: {missing}"
        )

    return template_path
