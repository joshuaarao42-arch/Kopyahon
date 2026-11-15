"""Typed, persistent application settings stored in the SQLite database."""
from __future__ import annotations

import json
import logging
from typing import Any

from .database import DUPLICATE_MODES, Database

log = logging.getLogger(__name__)

DEFAULTS: dict[str, Any] = {
    "theme": "dark",             # "dark" | "light"
    "monitoring": True,          # record clipboard text in the background
    "history_limit": 500,        # non-favorite clips kept
    "duplicate_mode": "move",    # "move" | "skip" | "allow"
    "notify_on_save": True,      # toast whenever a clip is recorded
}

_CHOICES = {
    "theme": ("dark", "light"),
    "duplicate_mode": DUPLICATE_MODES,
}


def _coerce(key: str, value: Any) -> Any:
    default = DEFAULTS[key]
    if isinstance(default, bool):
        return bool(value)
    if isinstance(default, int):
        value = int(value)
        return value if value >= 10 else default
    if key in _CHOICES:
        return value if value in _CHOICES[key] else default
    return value


class Settings:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._values: dict[str, Any] = dict(DEFAULTS)
        for key in DEFAULTS:
            raw = db.get_setting(key)
            if raw is None:
                continue
            try:
                self._values[key] = _coerce(key, json.loads(raw))
            except (ValueError, TypeError):
                log.warning("Ignoring invalid stored value for setting %r", key)

    def get(self, key: str) -> Any:
        return self._values[key]

    def set(self, key: str, value: Any) -> Any:
        if key not in DEFAULTS:
            raise KeyError(key)
        value = _coerce(key, value)
        self._values[key] = value
        self._db.set_setting(key, json.dumps(value))
        return value
