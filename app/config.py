"""Load environment variables from app/.env and optional repo-root .env."""

from __future__ import annotations

import os
from pathlib import Path


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
    here = Path(__file__).resolve()
    candidates = [
        here.parent / ".env",
        here.parents[1] / ".env",
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
