"""Build state persistence for Docsmith."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class BuildState:
    """Persisted document build state."""

    current_version: str
    last_fingerprint: str
    last_git_hash: str | None
    last_build_at: str


def state_file_path(build_dir: Path) -> Path:
    """Return the persisted state file path for a build directory."""
    return build_dir / ".docsmith-state.json"


def load_build_state(build_dir: Path) -> BuildState | None:
    """Load prior build state, if present."""
    path = state_file_path(build_dir)
    if not path.exists():
        return None

    raw_state = json.loads(path.read_text(encoding="utf-8"))
    return BuildState(
        current_version=raw_state["current_version"],
        last_fingerprint=raw_state["last_fingerprint"],
        last_git_hash=raw_state.get("last_git_hash"),
        last_build_at=raw_state["last_build_at"],
    )


def save_build_state(
    build_dir: Path,
    *,
    current_version: str,
    fingerprint: str,
    git_hash: str | None,
) -> Path:
    """Write build state after a successful render."""
    build_dir.mkdir(parents=True, exist_ok=True)
    path = state_file_path(build_dir)
    state = BuildState(
        current_version=current_version,
        last_fingerprint=fingerprint,
        last_git_hash=git_hash,
        last_build_at=datetime.now(timezone.utc).isoformat(),
    )
    path.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
    return path
