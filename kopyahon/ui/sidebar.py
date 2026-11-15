"""Left navigation rail with brand, page links and the monitoring control."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import assets, strings as T, theme
from ..constants import APP_NAME, VERSION
from ..icons import icon
from ..theme import C
from .components import button, label

NAV_ITEMS = (
    ("dashboard", "Dashboard", "dashboard"),
    ("history", "History", "history"),
    ("favorites", "Favorites", "star"),
    ("snippets", "Snippets", "snippet"),
    ("settings", "Settings", "settings"),
    ("about", "About", "about"),
)


class Sidebar(ctk.CTkFrame):
    WIDTH = 240

    def __init__(self, master, on_navigate: Callable[[str], None],
                 on_toggle_monitor: Callable[[], None]) -> None:
        super().__init__(master, width=self.WIDTH, corner_radius=0, fg_color=C["sidebar"])
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._buttons: dict[str, tuple[ctk.CTkButton, ctk.CTkFrame, str]] = {}
        self._active: str | None = None

        # right-hand hairline
        ctk.CTkFrame(self, width=1, corner_radius=0, fg_color=C["border"]).place(
            relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # brand
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(26, 22))
        ctk.CTkLabel(brand, text="", image=assets.load_logo(42)).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        label(brand, APP_NAME, 19, "bold").grid(row=0, column=1, sticky="sw")
        label(brand, "Clipboard history", 11, color="muted").grid(row=1, column=1, sticky="nw")

        # navigation
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=14)
        nav.grid_columnconfigure(0, weight=1)
        for row, (key, text, icon_name) in enumerate(NAV_ITEMS):
            item = ctk.CTkFrame(nav, fg_color="transparent")
            item.grid(row=row, column=0, sticky="ew", pady=2)
            item.grid_columnconfigure(1, weight=1)
            bar = ctk.CTkFrame(item, width=4, height=22, corner_radius=2, fg_color="transparent")
            bar.grid(row=0, column=0, padx=(0, 6))
            btn = ctk.CTkButton(
                item, text="  " + text, image=icon(icon_name, 19, "muted"), compound="left",
                anchor="w", height=42, corner_radius=theme.RADIUS_SM, fg_color="transparent",
                hover_color=C["card_hover"], text_color=C["muted"], font=theme.font(14),
                command=lambda k=key: on_navigate(k))
            btn.grid(row=0, column=1, sticky="ew")
            self._buttons[key] = (btn, bar, icon_name)

        # monitoring status card
        status = ctk.CTkFrame(self, fg_color=C["card_alt"], border_width=1,
                              border_color=C["border"], corner_radius=theme.RADIUS)
        status.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        status.grid_columnconfigure(1, weight=1)
        self.dot = label(status, "●", 12, color="success", width=14)
        self.dot.grid(row=0, column=0, padx=(16, 6), pady=(14, 0))
        self.status_text = label(status, T.STATUS_WATCHING, 14, "bold")
        self.status_text.grid(row=0, column=1, sticky="w", pady=(14, 0))
        self.status_sub = label(status, "Recording copied text", 11, color="muted")
        self.status_sub.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 10))
        self.toggle_btn = button(status, "Pause monitoring", on_toggle_monitor, "secondary",
                                 "pause", width=190, height=36)
        self.toggle_btn.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

        label(self, f"v{VERSION}  ·  {T.CAPTION_ABOUT}", 11, color="subtle").grid(
            row=4, column=0, sticky="w", padx=24, pady=(0, 18))

    # ---------------------------------------------------------------- API
    def set_active(self, key: str) -> None:
        for name, (btn, bar, icon_name) in self._buttons.items():
            if name == key:
                btn.configure(fg_color=C["accent_soft"], hover_color=C["accent_soft"],
                              text_color=C["accent"], image=icon(icon_name, 19, "accent"),
                              font=theme.font(14, "bold"))
                bar.configure(fg_color=C["accent"])
            else:
                btn.configure(fg_color="transparent", hover_color=C["card_hover"],
                              text_color=C["muted"], image=icon(icon_name, 19, "muted"),
                              font=theme.font(14))
                bar.configure(fg_color="transparent")
        self._active = key

    def set_monitoring(self, active: bool) -> None:
        if active:
            self.dot.configure(text_color=C["success"])
            self.status_text.configure(text=T.STATUS_WATCHING)
            self.status_sub.configure(text="Recording copied text")
            self.toggle_btn.configure(text="  Pause monitoring", image=icon("pause", 17, "text"))
        else:
            self.dot.configure(text_color=C["warning"])
            self.status_text.configure(text=T.STATUS_PAUSED)
            self.status_sub.configure(text="Nothing is being recorded")
            self.toggle_btn.configure(text="  Resume monitoring", image=icon("play", 17, "text"))
