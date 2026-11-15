"""Main window: wires the database, clipboard monitor and pages together."""
from __future__ import annotations

import logging
import queue
from typing import Optional

import customtkinter as ctk

from . import assets, strings as T, theme
from .clipboard_monitor import ClipboardMonitor
from .constants import APP_NAME, POLL_INTERVAL, TAGLINE
from .database import Database
from .settings import Settings
from .theme import C
from .ui.about import AboutPage
from .ui.clip_list import FavoritesPage, HistoryPage
from .ui.components import Toast, ask_confirm
from .ui.dashboard import DashboardPage
from .ui.page import Page
from .ui.settings_page import SettingsPage
from .ui.sidebar import Sidebar
from .ui.snippets import SnippetsPage

log = logging.getLogger(__name__)


class KopyahonApp(ctk.CTk):
    def __init__(self, db: Database, settings: Settings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self._clip_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._closing = False
        self._drain_job: Optional[str] = None
        self.current_name: Optional[str] = None

        self.title(f"{APP_NAME}  -  {TAGLINE}")
        self.configure(fg_color=C["bg"])
        theme.init_fonts(self)
        assets.ensure_assets()
        assets.apply_window_icon(self)
        self._place_window(1220, 780, 1040, 660)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---- layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = Sidebar(self, self.show_page, self.toggle_monitoring)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self.pages: dict[str, Page] = {
            "dashboard": DashboardPage(content, self),
            "history": HistoryPage(content, self),
            "favorites": FavoritesPage(content, self),
            "snippets": SnippetsPage(content, self),
            "settings": SettingsPage(content, self),
            "about": AboutPage(content, self),
        }
        self.toast = Toast(self)

        # ---- clipboard monitor (background thread -> queue -> Tk thread)
        self.monitor = ClipboardMonitor(
            on_clip=lambda text: self._clip_queue.put(("clip", text)),
            on_error=lambda msg: self._clip_queue.put(("error", msg)),
            interval=POLL_INTERVAL)
        self.monitor.start(paused=not settings.get("monitoring"))
        self.sidebar.set_monitoring(self.monitor.is_active)

        self.show_page("dashboard")
        self._drain_job = self.after(250, self._drain_events)

    # ----------------------------------------------------------- window
    def _place_window(self, width: int, height: int, min_w: int, min_h: int) -> None:
        try:
            scale = self._get_window_scaling()
        except Exception:
            scale = 1.0
        screen_w = self.winfo_screenwidth() / scale
        screen_h = self.winfo_screenheight() / scale
        width, height = int(min(width, screen_w * 0.94)), int(min(height, screen_h * 0.9))
        x = max(0, int((screen_w - width) / 2 * scale))
        y = max(0, int((screen_h - height) / 2 * scale * 0.8))
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min_w, min_h)

    def report_callback_exception(self, exc, val, tb) -> None:
        """Log UI callback errors and tell the user instead of failing silently."""
        log.error("Unhandled UI error", exc_info=(exc, val, tb))
        try:
            self.notify("Something went wrong - see kopyahon.log for details.", "error")
        except Exception:
            pass

    # ------------------------------------------------------- navigation
    def show_page(self, name: str, **kwargs) -> None:
        page = self.pages[name]
        current = self.pages.get(self.current_name) if self.current_name else None
        if current is not None and current is not page:
            current.grid_remove()
        page.grid(row=0, column=0, sticky="nsew")
        self.current_name = name
        self.sidebar.set_active(name)
        page.on_show(**kwargs)

    @property
    def current_page(self) -> Optional[Page]:
        return self.pages.get(self.current_name) if self.current_name else None

    def refresh_current(self) -> None:
        page = self.current_page
        if page is not None:
            page.refresh()

    # ------------------------------------------------------ notifications
    def notify(self, message: str, kind: str = "info") -> None:
        self.toast.show(message, kind)

    def ask_confirm(self, **kwargs) -> tuple[bool, bool]:
        return ask_confirm(self, **kwargs)

    # ----------------------------------------------------------- actions
    def copy_text(self, text: str, message: Optional[str] = None) -> None:
        try:
            self.monitor.copy_to_clipboard(text)
        except Exception as exc:
            log.warning("Copy failed: %s", exc)
            self.notify("Couldn't access the clipboard.", "error")
            return
        self.notify(message or T.TOAST_COPIED, "success")

    def toggle_favorite(self, clip_id: int) -> Optional[bool]:
        state = self.db.toggle_favorite(clip_id)
        if state is not None:
            self.notify(T.TOAST_FAV_ADDED if state else T.TOAST_FAV_REMOVED, "success")
        return state

    def delete_clips(self, ids) -> int:
        removed = self.db.delete_clips(ids)
        if removed:
            self.notify(T.TOAST_DELETED.format(n=removed), "success")
        return removed

    def clear_history(self, keep_favorites: bool) -> None:
        self.db.clear_history(keep_favorites)
        self.notify(T.TOAST_CLEARED, "success")
        self.refresh_current()

    def apply_history_limit(self, limit: int) -> None:
        self.settings.set("history_limit", limit)
        removed = self.db.prune(limit)
        if removed:
            self.notify(T.TOAST_DELETED.format(n=removed), "success")

    def apply_theme(self, mode: str) -> None:
        mode = self.settings.set("theme", mode)
        ctk.set_appearance_mode(mode)

    def set_monitoring(self, enabled: bool) -> None:
        self.settings.set("monitoring", enabled)
        if enabled:
            self.monitor.resume()
        else:
            self.monitor.pause()
        self.sidebar.set_monitoring(self.monitor.is_active)
        self.notify(T.TOAST_RESUMED if enabled else T.TOAST_PAUSED, "success" if enabled else "warning")
        self.refresh_current()

    def toggle_monitoring(self) -> None:
        self.set_monitoring(not self.monitor.is_active)

    # ------------------------------------------------- clipboard events
    def _drain_events(self) -> None:
        """Runs on the Tk thread: persist clips found by the background monitor."""
        self._drain_job = None
        if self._closing:
            return
        changed = False
        try:
            while True:
                kind, payload = self._clip_queue.get_nowait()
                if kind == "clip":
                    changed |= self._record_clip(payload)
                elif kind == "error":
                    self.notify("Can't read the clipboard right now. KOPYAHON will keep trying.", "error")
        except queue.Empty:
            pass
        if changed:
            self.refresh_current()
        self._drain_job = self.after(250, self._drain_events)

    def _record_clip(self, text: str) -> bool:
        try:
            result = self.db.add_clip(text, self.settings.get("duplicate_mode"),
                                      self.settings.get("history_limit"))
        except Exception:
            log.exception("Could not save clip")
            self.notify("Couldn't save the copied text.", "error")
            return False
        if result.status == "skipped":
            return False
        if self.settings.get("notify_on_save"):
            self.notify(T.TOAST_SAVED, "info")
        return True

    # ---------------------------------------------------------- shutdown
    def on_close(self) -> None:
        self._closing = True
        if self._drain_job is not None:
            try:
                self.after_cancel(self._drain_job)
            except Exception:
                pass
        try:
            self.monitor.stop()
        finally:
            self.db.close()
            self.destroy()
