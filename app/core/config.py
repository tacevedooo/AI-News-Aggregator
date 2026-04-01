"""Load environment variables from standard locations."""

from __future__ import annotations

import os
from pathlib import Path

# Repo root: app/core/config.py -> parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


def load_env() -> None:
    """Populate os.environ from .env files (does not override existing vars)."""
    candidates = [
        _REPO_ROOT / ".env",
        _REPO_ROOT / "app" / ".env",
        _REPO_ROOT / "config" / ".env",
    ]
    for env_path in candidates:
        if not env_path.exists():
            continue
        try:
            text = env_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw in text.splitlines():
            parsed = _parse_env_line(raw)
            if parsed:
                k, v = parsed
                os.environ.setdefault(k, v)
