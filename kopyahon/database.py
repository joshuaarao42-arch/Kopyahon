"""SQLite persistence for clips, snippets and settings.

A single connection is shared between the UI thread and background helpers,
guarded by a re-entrant lock, so it is safe to call from any thread.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NamedTuple, Optional

from .utils import now_iso, sha256_text, today_start_iso

SCHEMA_VERSION = 1

SORT_ORDERS = {
    "newest": "created_at DESC, id DESC",
    "oldest": "created_at ASC, id ASC",
    "longest": "char_count DESC, id DESC",
    "shortest": "char_count ASC, id DESC",
    "alphabetical": "PYLOWER(content) ASC, id DESC",
}

DUPLICATE_MODES = ("move", "skip", "allow")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    content       TEXT    NOT NULL,
    content_hash  TEXT    NOT NULL,
    char_count    INTEGER NOT NULL,
    favorite      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clips_created ON clips(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clips_hash    ON clips(content_hash);
CREATE INDEX IF NOT EXISTS idx_clips_fav     ON clips(favorite);

CREATE TABLE IF NOT EXISTS snippets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Clip:
    id: int
    content: str
    created_at: str
    favorite: bool
    char_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Clip":
        return cls(
            id=row["id"],
            content=row["content"],
            created_at=row["created_at"],
            favorite=bool(row["favorite"]),
            char_count=row["char_count"],
        )


@dataclass(frozen=True)
class Snippet:
    id: int
    title: str
    content: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Snippet":
        return cls(row["id"], row["title"], row["content"], row["created_at"], row["updated_at"])


class AddResult(NamedTuple):
    status: str               # "added" | "moved" | "skipped"
    clip_id: Optional[int]
    pruned: int               # old clips removed to honour the history limit


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _py_lower(value):
    return value.lower() if isinstance(value, str) else value


class Database:
    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # SQLite's LIKE/lower() only fold ASCII; this makes search Unicode-aware.
        self._conn.create_function("PYLOWER", 1, _py_lower, deterministic=True)
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON")
            try:
                self._conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.DatabaseError:
                pass
            self._conn.executescript(_SCHEMA)
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            self._conn.commit()

    # ------------------------------------------------------------ lifecycle
    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass

    # ---------------------------------------------------------------- clips
    @staticmethod
    def _where(search: str, favorites_only: bool) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if favorites_only:
            clauses.append("favorite = 1")
        for term in (search or "").split():
            clauses.append("PYLOWER(content) LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(term.lower())}%")
        return (" WHERE " + " AND ".join(clauses)) if clauses else "", params

    def add_clip(self, content: str, duplicate_mode: str = "move",
                 history_limit: Optional[int] = None) -> AddResult:
        if duplicate_mode not in DUPLICATE_MODES:
            duplicate_mode = "move"
        digest = sha256_text(content)
        with self._lock, self._conn:
            existing = self._conn.execute(
                "SELECT id FROM clips WHERE content_hash = ? AND content = ? "
                "ORDER BY id DESC LIMIT 1", (digest, content)).fetchone()
            if existing and duplicate_mode != "allow":
                if duplicate_mode == "skip":
                    return AddResult("skipped", existing["id"], 0)
                self._conn.execute("UPDATE clips SET created_at = ? WHERE id = ?",
                                   (now_iso(), existing["id"]))
                return AddResult("moved", existing["id"], 0)
            cur = self._conn.execute(
                "INSERT INTO clips (content, content_hash, char_count, favorite, created_at) "
                "VALUES (?, ?, ?, 0, ?)", (content, digest, len(content), now_iso()))
            clip_id = cur.lastrowid
            pruned = self._prune_locked(history_limit) if history_limit else 0
            return AddResult("added", clip_id, pruned)

    def _prune_locked(self, limit: int) -> int:
        cur = self._conn.execute(
            "DELETE FROM clips WHERE favorite = 0 AND id NOT IN ("
            "  SELECT id FROM clips WHERE favorite = 0 "
            "  ORDER BY created_at DESC, id DESC LIMIT ?)", (int(limit),))
        return cur.rowcount

    def prune(self, limit: int) -> int:
        """Delete the oldest non-favorite clips beyond ``limit``. Favorites are kept."""
        with self._lock, self._conn:
            return self._prune_locked(limit)

    def count_prunable(self, limit: int) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM clips WHERE favorite = 0").fetchone()
        return max(0, row["n"] - int(limit))

    def get_clips(self, search: str = "", sort: str = "newest", favorites_only: bool = False,
                  limit: Optional[int] = None, offset: int = 0) -> list[Clip]:
        where, params = self._where(search, favorites_only)
        order = SORT_ORDERS.get(sort, SORT_ORDERS["newest"])
        sql = f"SELECT * FROM clips{where} ORDER BY {order}"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = params + [int(limit), int(offset)]
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [Clip.from_row(r) for r in rows]

    def count_clips(self, search: str = "", favorites_only: bool = False) -> int:
        where, params = self._where(search, favorites_only)
        with self._lock:
            return self._conn.execute(f"SELECT COUNT(*) AS n FROM clips{where}", params).fetchone()["n"]

    def get_clip(self, clip_id: int) -> Optional[Clip]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
        return Clip.from_row(row) if row else None

    def get_latest_clip(self) -> Optional[Clip]:
        clips = self.get_clips(sort="newest", limit=1)
        return clips[0] if clips else None

    def stats(self) -> dict[str, int]:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS total, "
                "COALESCE(SUM(created_at >= ?), 0) AS today, "
                "COALESCE(SUM(favorite), 0) AS favorites FROM clips", (today_start_iso(),)).fetchone()
        return {"total": row["total"], "today": row["today"], "favorites": row["favorites"]}

    def set_favorite(self, clip_id: int, favorite: bool) -> None:
        with self._lock, self._conn:
            self._conn.execute("UPDATE clips SET favorite = ? WHERE id = ?", (1 if favorite else 0, clip_id))

    def toggle_favorite(self, clip_id: int) -> Optional[bool]:
        """Flip the favorite flag. Returns the new state, or None if the clip is gone."""
        with self._lock, self._conn:
            row = self._conn.execute("SELECT favorite FROM clips WHERE id = ?", (clip_id,)).fetchone()
            if row is None:
                return None
            new_state = 0 if row["favorite"] else 1
            self._conn.execute("UPDATE clips SET favorite = ? WHERE id = ?", (new_state, clip_id))
            return bool(new_state)

    def delete_clips(self, ids: Iterable[int]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        with self._lock, self._conn:
            cur = self._conn.executemany("DELETE FROM clips WHERE id = ?", [(i,) for i in ids])
            return cur.rowcount

    def clear_history(self, keep_favorites: bool = True) -> int:
        sql = "DELETE FROM clips WHERE favorite = 0" if keep_favorites else "DELETE FROM clips"
        with self._lock, self._conn:
            return self._conn.execute(sql).rowcount

    # ------------------------------------------------------------- snippets
    def add_snippet(self, title: str, content: str) -> int:
        stamp = now_iso()
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO snippets (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title.strip(), content, stamp, stamp))
            return cur.lastrowid

    def update_snippet(self, snippet_id: int, title: str, content: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE snippets SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                (title.strip(), content, now_iso(), snippet_id))

    def delete_snippet(self, snippet_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))

    def get_snippet(self, snippet_id: int) -> Optional[Snippet]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,)).fetchone()
        return Snippet.from_row(row) if row else None

    def get_snippets(self, search: str = "") -> list[Snippet]:
        clauses, params = [], []
        for term in (search or "").split():
            clauses.append("(PYLOWER(title) LIKE ? ESCAPE '\\' OR PYLOWER(content) LIKE ? ESCAPE '\\')")
            like = f"%{_escape_like(term.lower())}%"
            params += [like, like]
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM snippets{where} ORDER BY updated_at DESC, id DESC", params).fetchall()
        return [Snippet.from_row(r) for r in rows]

    def count_snippets(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) AS n FROM snippets").fetchone()["n"]

    # ------------------------------------------------------------- settings
    def get_setting(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
