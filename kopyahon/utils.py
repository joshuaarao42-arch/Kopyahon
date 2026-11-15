"""Small, dependency-free helpers shared across KOPYAHON."""
from __future__ import annotations

import getpass
import hashlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import strings as T
from .constants import APP_ID, APP_NAME

ISO_FORMAT = "%Y-%m-%d %H:%M:%S.%f"      # microseconds keep ordering stable
_ISO_FALLBACK = "%Y-%m-%d %H:%M:%S"


# --------------------------------------------------------------------- paths
def get_data_dir() -> Path:
    """Folder that holds the SQLite database and log file (created on demand)."""
    override = os.environ.get("KOPYAHON_DATA_DIR")
    if override:
        path = Path(override).expanduser()
    elif sys.platform.startswith("win"):
        path = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        path = Path(base) / APP_NAME.lower()
    path.mkdir(parents=True, exist_ok=True)
    return path


def assets_dir() -> Path:
    """Locate the bundled assets folder (works from source and PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "assets"


def open_folder(path: Path | str) -> None:
    path = str(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def set_windows_app_id() -> None:
    """Make Windows show the KOPYAHON icon on the taskbar instead of Python's."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)  # type: ignore[attr-defined]
    except Exception:
        pass


# ---------------------------------------------------------------------- text
def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def normalize_newlines(text: str) -> str:
    """For *display only* - stored text is never altered."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def make_preview(text: str, max_lines: int = 2, max_chars: int = 180) -> str:
    lines = [ln.strip() for ln in normalize_newlines(text).split("\n") if ln.strip()]
    preview = "\n".join(lines[:max_lines])
    truncated = len(lines) > max_lines or len(preview) > max_chars
    preview = preview[:max_chars]
    return preview.rstrip() + " …" if truncated else preview


def text_stats(text: str) -> tuple[int, int, int]:
    """Return (characters, words, lines)."""
    normalized = normalize_newlines(text)
    return len(text), len(text.split()), normalized.count("\n") + 1


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


# --------------------------------------------------------------------- dates
def now_iso() -> str:
    return datetime.now().strftime(ISO_FORMAT)


def today_start_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d 00:00:00")


def parse_iso(value: str) -> datetime:
    for fmt in (ISO_FORMAT, _ISO_FALLBACK):
        try:
            return datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            continue
    return datetime.now()


def _clock(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def format_timestamp(value: str) -> str:
    dt = parse_iso(value)
    return f"{dt.day} {dt:%b %Y} · {_clock(dt)}"


def format_long_date(dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    return f"{dt:%A}, {dt.day} {dt:%B %Y}"


def time_ago(value: str) -> str:
    dt = parse_iso(value)
    seconds = max(0, int((datetime.now() - dt).total_seconds()))
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    if seconds < 7 * 86400:
        return f"{seconds // 86400} d ago"
    return f"{dt.day} {dt:%b %Y}"


def greeting(now: datetime | None = None) -> str:
    hour = (now or datetime.now()).hour
    if 5 <= hour < 11:
        return T.GREETING_MORNING
    if 11 <= hour < 13:
        return T.GREETING_NOON
    if 13 <= hour < 18:
        return T.GREETING_AFTERNOON
    return T.GREETING_EVENING


def display_name() -> str:
    try:
        name = getpass.getuser()
    except Exception:
        name = ""
    name = name.replace("_", " ").replace(".", " ").strip()
    return name.split()[0].title() if name else T.FRIEND
