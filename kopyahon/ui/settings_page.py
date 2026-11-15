"""Settings: theme, monitoring, history limit, duplicates, data and privacy."""
from __future__ import annotations

import customtkinter as ctk

from .. import strings as T, theme, utils
from ..constants import HISTORY_LIMITS
from ..theme import C
from .components import (button, card, divider, label, option_menu, page_header, switch)
from .page import Page

DUPLICATE_LABELS = {
    "move": "Move existing to top",
    "skip": "Ignore duplicates",
    "allow": "Keep every copy",
}
LIMIT_LABELS = {f"{n:,} clips": n for n in HISTORY_LIMITS}

PRIVACY_POINTS = (
    "KOPYAHON records text only while it is open and monitoring is on - the sidebar always shows which.",
    "Everything is stored locally in a SQLite file on this computer. Nothing is ever sent over a network.",
    "Anything copied while monitoring is paused is never saved, even after you resume.",
    "Tip: pause monitoring before copying passwords or other secrets.",
)


class SettingsPage(Page):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.grid_rowconfigure(1, weight=1)
        self._syncing = False

        header = page_header(self, T.CAPTION_SETTINGS, "Settings", "Make KOPYAHON work your way.")
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, 14))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        scroll.grid(row=1, column=0, sticky="nsew", padx=(theme.PAD, theme.PAD - 8), pady=(0, theme.PAD))
        scroll.grid_columnconfigure(0, weight=1)

        # ---- Appearance
        appearance = self._section(scroll, 0, "Appearance")
        self.theme_seg = ctk.CTkSegmentedButton(
            appearance, values=["Dark", "Light"], command=self._on_theme, width=190, height=36,
            corner_radius=theme.RADIUS_SM, fg_color=C["card_alt"], selected_color=C["accent_mid"],
            selected_hover_color=C["accent_mid"], unselected_color=C["card_alt"],
            unselected_hover_color=C["card_hover"], text_color=C["text"], font=theme.font(13, "bold"))
        self._row(appearance, 1, "Theme", "Dark is the default. Changes apply instantly.", self.theme_seg)

        # ---- Clipboard
        clipboard = self._section(scroll, 1, "Clipboard monitoring")
        self.monitor_switch = switch(clipboard, command=self._on_monitoring)
        self._row(clipboard, 1, "Record copied text",
                  "Watch the clipboard in the background and save new text to your history.",
                  self.monitor_switch)
        self.notify_switch = switch(clipboard, command=self._on_notify)
        self._row(clipboard, 3, "Notify when a clip is saved",
                  "Show a small message each time something new is recorded.", self.notify_switch)

        # ---- History
        history = self._section(scroll, 2, "History")
        self.limit_menu = option_menu(history, LIMIT_LABELS.keys(), self._on_limit, width=170)
        self._row(history, 1, "Maximum history",
                  "Oldest clips are removed first. Favorites are never removed automatically.",
                  self.limit_menu)
        self.dup_menu = option_menu(history, DUPLICATE_LABELS.values(), self._on_duplicates, width=210)
        self._row(history, 3, "When you copy something again",
                  "Choose what happens if the text is already in your history.", self.dup_menu)
        clear_btn = button(history, "Clear history…", self._clear_history, "danger", "trash", width=170)
        self._row(history, 5, "Clear history", "Permanently delete saved clips. Snippets are not affected.",
                  clear_btn)

        # ---- Data & privacy
        data = self._section(scroll, 3, "Your data & privacy")
        folder_btn = button(data, "Open folder", self._open_folder, "secondary", "folder", width=150)
        self._row(data, 1, "Data location", str(utils.get_data_dir()), folder_btn, wrap=420)
        divider(data).grid(row=3, column=0, columnspan=2, sticky="ew", padx=20)
        points = ctk.CTkFrame(data, fg_color="transparent")
        points.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(14, 18))
        for i, text in enumerate(PRIVACY_POINTS):
            label(points, "●", 8, color="accent", width=14).grid(row=i, column=0, sticky="n", pady=(5, 0))
            label(points, text, 12, color="muted", wraplength=640).grid(row=i, column=1, sticky="w", pady=2)

    # ------------------------------------------------------------- layout
    def _section(self, parent, row: int, title: str) -> ctk.CTkFrame:
        frame = card(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, theme.GAP), padx=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        label(frame, title, 15, "bold").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 4))
        return frame

    def _row(self, frame, row: int, title: str, description: str, control, wrap: int = 460) -> None:
        if row > 1:
            divider(frame).grid(row=row - 1, column=0, columnspan=2, sticky="ew", padx=20)
        text = ctk.CTkFrame(frame, fg_color="transparent")
        text.grid(row=row, column=0, sticky="w", padx=20, pady=12)
        label(text, title, 14, "bold").grid(row=0, column=0, sticky="w")
        label(text, description, 12, color="muted", wraplength=wrap).grid(row=1, column=0, sticky="w", pady=(2, 0))
        control.grid(row=row, column=1, sticky="e", padx=20, pady=12)

    # ------------------------------------------------------------ refresh
    def refresh(self) -> None:
        s = self.app.settings
        self._syncing = True
        try:
            self.theme_seg.set("Dark" if s.get("theme") == "dark" else "Light")
            (self.monitor_switch.select if s.get("monitoring") else self.monitor_switch.deselect)()
            (self.notify_switch.select if s.get("notify_on_save") else self.notify_switch.deselect)()
            limit = s.get("history_limit")
            self.limit_menu.set(next((k for k, v in LIMIT_LABELS.items() if v == limit), f"{limit:,} clips"))
            self.dup_menu.set(DUPLICATE_LABELS[s.get("duplicate_mode")])
        finally:
            self._syncing = False

    # ----------------------------------------------------------- handlers
    def _on_theme(self, value: str) -> None:
        self.app.apply_theme(value.lower())

    def _on_monitoring(self) -> None:
        if self._syncing:
            return
        self.app.set_monitoring(bool(self.monitor_switch.get()))

    def _on_notify(self) -> None:
        if not self._syncing:
            self.app.settings.set("notify_on_save", bool(self.notify_switch.get()))

    def _on_limit(self, choice: str) -> None:
        limit = LIMIT_LABELS[choice]
        removable = self.app.db.count_prunable(limit)
        if removable:
            confirmed, _ = self.app.ask_confirm(
                title="Lower the history limit?",
                message=f"{utils.plural(removable, 'older clip')} will be deleted to fit the new limit "
                        "(favorites are kept).",
                confirm_text="Delete & apply", danger=True)
            if not confirmed:
                self.refresh()          # put the menu back
                return
        self.app.apply_history_limit(limit)

    def _on_duplicates(self, choice: str) -> None:
        mode = next(k for k, v in DUPLICATE_LABELS.items() if v == choice)
        self.app.settings.set("duplicate_mode", mode)

    def _clear_history(self) -> None:
        total = self.app.db.count_clips()
        if total == 0:
            self.app.notify(T.EMPTY_HISTORY_TITLE, "warning")
            return
        confirmed, keep = self.app.ask_confirm(
            title="Clear clipboard history?",
            message=f"This permanently deletes your saved clips ({total:,}). This can't be undone.",
            confirm_text="Clear history", danger=True,
            checkbox_text="Keep my favorites", checkbox_default=True)
        if confirmed:
            self.app.clear_history(keep_favorites=keep)

    def _open_folder(self) -> None:
        try:
            utils.open_folder(utils.get_data_dir())
        except Exception as exc:
            self.app.notify(f"Couldn't open the folder: {exc}", "error")
