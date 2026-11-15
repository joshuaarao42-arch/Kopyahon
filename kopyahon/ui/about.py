"""About: logo, version, credits and technology."""
from __future__ import annotations

import customtkinter as ctk

from .. import assets, strings as T, theme, utils
from ..constants import APP_NAME, AUTHOR, DESCRIPTION, TAGLINE, VERSION
from ..theme import C
from .components import button, card, divider, label, page_header
from .page import Page

STACK = ("Python 3", "CustomTkinter", "SQLite", "Pillow", "Pyperclip")


class AboutPage(Page):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.grid_rowconfigure(1, weight=1)
        header = page_header(self, T.CAPTION_ABOUT, f"About {APP_NAME}")
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, 14))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        scroll.grid(row=1, column=0, sticky="nsew", padx=(theme.PAD, theme.PAD - 8), pady=(0, theme.PAD))
        scroll.grid_columnconfigure(0, weight=1)

        hero = card(scroll)
        hero.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, theme.GAP))
        hero.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hero, text="", image=assets.load_logo(120)).grid(
            row=0, column=0, rowspan=4, padx=28, pady=28)
        label(hero, APP_NAME, 32, "bold").grid(row=0, column=1, sticky="sw", pady=(28, 0))
        label(hero, TAGLINE, 15, "bold", "accent").grid(row=1, column=1, sticky="w")
        label(hero, DESCRIPTION, 13, color="muted", wraplength=520).grid(
            row=2, column=1, sticky="w", pady=(8, 0), padx=(0, 28))
        label(hero, f"Version {VERSION}", 12, "bold", "subtle").grid(
            row=3, column=1, sticky="nw", pady=(8, 28))

        info = card(scroll)
        info.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, theme.GAP))
        info.grid_columnconfigure(1, weight=1)
        rows = (
            ("Version", VERSION),
            ("Developer", AUTHOR),
            ("Name", "From the Cebuano word “kopya” - a copy"),
            ("Storage", f"Local SQLite database in {utils.get_data_dir()}"),
            ("Privacy", "Works offline. Clipboard data never leaves this computer."),
        )
        for i, (key, value) in enumerate(rows):
            if i:
                divider(info).grid(row=i * 2 - 1, column=0, columnspan=2, sticky="ew", padx=20)
            label(info, key, 13, "bold", "muted", width=110).grid(row=i * 2, column=0, sticky="nw", padx=(20, 10), pady=12)
            label(info, value, 13, wraplength=520).grid(row=i * 2, column=1, sticky="w", padx=(0, 20), pady=12)

        stack = card(scroll)
        stack.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(0, theme.GAP))
        label(stack, "Built with", 15, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))
        chips = ctk.CTkFrame(stack, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 18))
        for i, name in enumerate(STACK):
            chip = ctk.CTkFrame(chips, fg_color=C["accent_soft"], corner_radius=16)
            chip.grid(row=0, column=i, padx=4)
            label(chip, name, 12, "bold", "accent").grid(row=0, column=0, padx=14, pady=6)

        label(scroll, f"Made with care. {TAGLINE}", 12, color="subtle", anchor="center").grid(
            row=3, column=0, pady=(4, 0))
