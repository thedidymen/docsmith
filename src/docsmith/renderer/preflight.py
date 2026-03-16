"""External tool checks for PDF rendering."""

from __future__ import annotations

import shutil
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in bare environments.
    yaml = None

from docsmith.renderer.defaults import template_defaults_path


def _read_pdf_engine(defaults_file: Path) -> str | None:
    """Read the configured PDF engine from template defaults."""
    if not defaults_file.exists():
        return None

    raw_text = defaults_file.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(raw_text) or {}
        if isinstance(loaded, dict):
            engine = loaded.get("pdf-engine")
            return str(engine) if engine else None

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if line.startswith("pdf-engine:"):
            _, _, value = line.partition(":")
            candidate = value.strip()
            return candidate or None

    return None


def required_pdf_dependencies(template_root: Path) -> list[str]:
    """Return external executables required for PDF rendering."""
    dependencies = ["pandoc"]
    pdf_engine = _read_pdf_engine(template_defaults_path(template_root))
    if pdf_engine:
        dependencies.append(pdf_engine)
    return dependencies


def validate_pdf_dependencies(template_root: Path) -> list[str]:
    """Return missing external executables required for PDF rendering."""
    return [
        executable
        for executable in required_pdf_dependencies(template_root)
        if shutil.which(executable) is None
    ]


def describe_missing_pdf_dependencies(missing_dependencies: list[str]) -> str:
    """Render an actionable message for missing PDF build tools."""
    missing = ", ".join(missing_dependencies)
    commands = ", ".join(f"`{name} --version`" for name in missing_dependencies)
    return (
        f"Missing external PDF build dependencies: {missing}. "
        f"Install them and confirm they are on PATH with {commands}."
    )
