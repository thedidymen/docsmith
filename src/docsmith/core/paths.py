"""Path resolution helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_document_path(path: str | Path, base_dir: Path) -> Path:
    """Resolve a path relative to a document base directory."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()

