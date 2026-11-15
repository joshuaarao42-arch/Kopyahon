"""Base class shared by all pages."""
from __future__ import annotations

import customtkinter as ctk


class Page(ctk.CTkFrame):
    """A full-window page. ``on_show`` runs each time it becomes visible."""

    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)

    def on_show(self, **kwargs) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Re-read data / state and update widgets. Must be cheap and safe to repeat."""
