"""Text Snippets: create, edit, delete and copy frequently used text."""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from .. import strings as T, theme, utils
from ..database import Snippet
from ..theme import C
from .components import (EmptyState, SearchBar, _ModalDialog, button, card, icon_button, label,
                         page_header)
from .page import Page


class SnippetDialog(_ModalDialog):
    """Modal editor. ``result`` is ``(title, content)`` after Save, otherwise ``None``."""

    def __init__(self, parent, snippet: Optional[Snippet] = None) -> None:
        super().__init__(parent, "Edit snippet" if snippet else "New snippet", 520, 470)
        self.result: Optional[tuple[str, str]] = None
        body = card(self)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)
        label(body, "Edit snippet" if snippet else "New snippet", 17, "bold").grid(
            row=0, column=0, sticky="w", padx=22, pady=(20, 12))
        label(body, "Title", 12, "bold", "muted").grid(row=1, column=0, sticky="w", padx=22)
        self.title_entry = ctk.CTkEntry(
            body, placeholder_text="e.g. Email sign-off", height=40, corner_radius=theme.RADIUS_SM,
            fg_color=C["input"], border_color=C["border"], text_color=C["text"],
            placeholder_text_color=C["subtle"], font=theme.font(13))
        self.title_entry.grid(row=2, column=0, sticky="ew", padx=22, pady=(4, 12))
        text_wrap = ctk.CTkFrame(body, fg_color="transparent")
        text_wrap.grid(row=3, column=0, sticky="nsew", padx=22)
        text_wrap.grid_columnconfigure(0, weight=1)
        text_wrap.grid_rowconfigure(1, weight=1)
        label(text_wrap, "Text", 12, "bold", "muted").grid(row=0, column=0, sticky="w")
        self.text = ctk.CTkTextbox(
            text_wrap, wrap="word", font=theme.mono(12), fg_color=C["input"], text_color=C["text"],
            border_width=1, border_color=C["border"], corner_radius=theme.RADIUS_SM)
        self.text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.error = label(body, "", 12, color="danger")
        self.error.grid(row=4, column=0, sticky="w", padx=22, pady=(8, 0))
        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="e", padx=22, pady=(8, 18))
        button(buttons, "Cancel", self.cancel, "secondary", width=100).grid(row=0, column=0, padx=(0, 10))
        button(buttons, "Save snippet", self._save, "primary", width=130).grid(row=0, column=1)
        if snippet:
            self.title_entry.insert(0, snippet.title)
            self.text.insert("1.0", utils.normalize_newlines(snippet.content))
        self.after(200, self.title_entry.focus_set)

    def _save(self) -> None:
        title = self.title_entry.get().strip()
        content = self.text.get("1.0", "end-1c")
        if not title:
            self.error.configure(text="Please give the snippet a title.")
            return
        if not content.strip():
            self.error.configure(text="The snippet text can't be empty.")
            return
        self.result = (title, content)
        self.destroy()


class SnippetsPage(Page):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.query = ""
        self.grid_rowconfigure(2, weight=1)

        header = page_header(self, T.CAPTION_SNIPPETS, "Text Snippets",
                             "Reusable text, one click from your clipboard.")
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, 14))
        button(header.actions, "New snippet", self.new_snippet, "primary", "plus", width=150).grid(row=0, column=0)

        self.search = SearchBar(self, "Search snippets…", on_change=self._on_search)
        self.search.grid(row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, 12))

        self.list = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        self.list.grid(row=2, column=0, sticky="nsew", padx=(theme.PAD, theme.PAD - 8), pady=(0, theme.PAD))
        self.list.grid_columnconfigure(0, weight=1)

    def on_show(self, new: bool = False, **kwargs) -> None:
        self.refresh()
        if new:
            self.after(60, self.new_snippet)

    def refresh(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        snippets = self.app.db.get_snippets(self.query)
        if not snippets:
            if self.query:
                EmptyState(self.list, "search", T.EMPTY_SEARCH_TITLE,
                           "No snippet matches your search.").grid(row=0, column=0, sticky="ew")
            else:
                EmptyState(self.list, "snippet", T.EMPTY_SNIPPETS_TITLE,
                           "Save text you type again and again - signatures, links, replies.",
                           "Create a snippet", self.new_snippet).grid(row=0, column=0, sticky="ew")
            return
        for index, snip in enumerate(snippets):
            self._build_card(index, snip)

    def _build_card(self, index: int, snip: Snippet) -> None:
        item = card(self.list)
        item.grid(row=index, column=0, sticky="ew", pady=(0, 10), padx=(0, 8))
        item.grid_columnconfigure(0, weight=1)
        label(item, snip.title, 15, "bold", wraplength=560).grid(
            row=0, column=0, sticky="w", padx=20, pady=(16, 0))
        label(item, utils.make_preview(snip.content, max_lines=3, max_chars=260), 12, color="muted",
              wraplength=560, font=theme.mono(12)).grid(row=1, column=0, sticky="w", padx=20, pady=(6, 0))
        label(item, f"Updated {utils.time_ago(snip.updated_at)}  ·  {utils.plural(len(snip.content), 'char')}",
              11, color="subtle").grid(row=2, column=0, sticky="w", padx=20, pady=(8, 16))
        actions = ctk.CTkFrame(item, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=3, padx=16)
        button(actions, "Copy", lambda s=snip: self.copy(s), "secondary", "copy",
               width=96, height=34).grid(row=0, column=0, padx=(0, 6))
        icon_button(actions, "edit", lambda s=snip: self.edit(s)).grid(row=0, column=1)
        icon_button(actions, "trash", lambda s=snip: self.delete(s), color="danger").grid(row=0, column=2)

    # --------------------------------------------------------------- actions
    def _on_search(self, text: str) -> None:
        self.query = text
        self.refresh()

    def copy(self, snip: Snippet) -> None:
        self.app.copy_text(snip.content)

    def new_snippet(self) -> None:
        dialog = SnippetDialog(self.app)
        self.app.wait_window(dialog)
        if dialog.result:
            self.app.db.add_snippet(*dialog.result)
            self.app.notify(T.TOAST_SNIPPET_SAVED, "success")
            self.refresh()

    def edit(self, snip: Snippet) -> None:
        dialog = SnippetDialog(self.app, snip)
        self.app.wait_window(dialog)
        if dialog.result:
            self.app.db.update_snippet(snip.id, *dialog.result)
            self.app.notify(T.TOAST_SNIPPET_SAVED, "success")
            self.refresh()

    def delete(self, snip: Snippet) -> None:
        confirmed, _ = self.app.ask_confirm(
            title="Delete this snippet?", message=f"“{snip.title}” will be removed permanently.",
            confirm_text="Delete", danger=True)
        if confirmed:
            self.app.db.delete_snippet(snip.id)
            self.app.notify(T.TOAST_SNIPPET_DELETED, "success")
            self.refresh()
