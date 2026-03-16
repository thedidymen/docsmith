"""Template defaults helpers."""

from __future__ import annotations

from pathlib import Path


def template_defaults_path(template_root: Path) -> Path:
    """Return the expected defaults file for a template."""
    return template_root / "defaults.yaml"

