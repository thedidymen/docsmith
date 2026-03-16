"""Git metadata helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_git_short_hash(repository_root: Path) -> str | None:
    """Return the current git short hash for a path, or ``None`` outside git."""
    repository_root = repository_root.resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=repository_root,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    git_hash = result.stdout.strip()
    return git_hash or None
