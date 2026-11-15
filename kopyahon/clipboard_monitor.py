"""Background clipboard watcher.

The monitor polls the clipboard on a daemon thread and reports *new* text to a
callback. It never touches the UI directly - the app drains a queue on the Tk
thread - and it only runs while the user has monitoring switched on.

Transparency rules baked in here:
  * Whatever is on the clipboard when monitoring starts or resumes is treated
    as a baseline and is NOT recorded. Text copied while paused is never saved.
  * Unchanged content is never reported twice.
  * Text KOPYAHON itself puts on the clipboard (copy-back) is not re-recorded.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from .constants import MAX_CLIP_CHARS, POLL_INTERVAL

log = logging.getLogger(__name__)


def _default_read() -> str:
    import pyperclip

    return pyperclip.paste()


def _default_write(text: str) -> None:
    import pyperclip

    pyperclip.copy(text)


class ClipboardMonitor:
    ERROR_THRESHOLD = 3   # consecutive failures before the user is told

    def __init__(self,
                 on_clip: Callable[[str], None],
                 on_error: Optional[Callable[[str], None]] = None,
                 read: Optional[Callable[[], str]] = None,
                 write: Optional[Callable[[str], None]] = None,
                 interval: float = POLL_INTERVAL,
                 max_chars: int = MAX_CLIP_CHARS) -> None:
        self._on_clip = on_clip
        self._on_error = on_error
        self._read = read or _default_read
        self._write = write or _default_write
        self.interval = interval
        self.max_chars = max_chars

        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._active = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_seen: Optional[str] = None
        self._failures = 0
        self._error_reported = False

    # --------------------------------------------------------------- state
    @property
    def is_active(self) -> bool:
        return self._active.is_set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------- control
    def start(self, paused: bool = False) -> None:
        if self.is_running:
            return
        self._stop.clear()
        self._sync_baseline()
        if not paused:
            self._active.set()
        self._thread = threading.Thread(target=self._run, name="kopyahon-clipboard", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._active.clear()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def pause(self) -> None:
        self._active.clear()

    def resume(self) -> None:
        self._sync_baseline()      # ignore anything copied while paused
        self._active.set()

    def copy_to_clipboard(self, text: str) -> None:
        """Put text on the clipboard without it being recorded as a new clip."""
        with self._lock:
            self._write(text)
            self._last_seen = text

    # ------------------------------------------------------------ internals
    def _sync_baseline(self) -> None:
        with self._lock:
            try:
                value = self._read()
                self._last_seen = value if isinstance(value, str) else None
            except Exception as exc:  # clipboard unavailable right now
                log.debug("Could not read baseline clipboard: %s", exc)
                self._last_seen = None

    def check_now(self) -> Optional[str]:
        """Poll once. Returns the text that was reported, if any (handy for tests)."""
        with self._lock:
            text = self._read()
            if not isinstance(text, str) or text == self._last_seen:
                return None
            self._last_seen = text
        if not text.strip() or len(text) > self.max_chars:
            return None
        try:
            self._on_clip(text)
        except Exception:
            log.exception("Clip callback failed")
        return text

    def _notify_error(self, message: str) -> None:
        if self._on_error is None:
            return
        try:
            self._on_error(message)
        except Exception:
            log.exception("Error callback failed")

    def _run(self) -> None:
        while not self._stop.is_set():
            delay = self.interval
            if self._active.is_set():
                try:
                    self.check_now()
                    self._failures = 0
                    self._error_reported = False
                except Exception as exc:
                    self._failures += 1
                    log.warning("Clipboard read failed (%d): %s", self._failures, exc)
                    if self._failures >= self.ERROR_THRESHOLD:
                        delay = min(5.0, self.interval * self._failures)
                        if not self._error_reported:
                            self._error_reported = True
                            self._notify_error(str(exc) or exc.__class__.__name__)
            self._stop.wait(delay)
