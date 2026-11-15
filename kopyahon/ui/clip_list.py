"""History and Favorites: searchable list, bulk selection and a preview pane."""
from __future__ import annotations

import dataclasses
from typing import Callable, Optional

import customtkinter as ctk

from .. import strings as T, theme, utils
from ..constants import PAGE_SIZE
from ..database import Clip
from ..icons import icon
from ..theme import C
from .components import (EmptyState, SearchBar, button, card, icon_button, label,
                         option_menu, page_header)
from .page import Page

SORT_OPTIONS = {
    "Newest first": "newest",
    "Oldest first": "oldest",
    "Longest first": "longest",
    "Shortest first": "shortest",
    "A → Z": "alphabetical",
}
PREVIEW_WIDTH = 340


class ClipRow(ctk.CTkFrame):
    """One clip in the list: checkbox, two-line preview, metadata and actions."""

    def __init__(self, master, clip: Clip, *, checked: bool, active: bool,
                 on_select: Callable[[int], None], on_check: Callable[[int, bool], None],
                 on_copy: Callable[[Clip], None], on_favorite: Callable[[int], None],
                 on_delete: Callable[[int], None], wraplength: int) -> None:
        super().__init__(master, fg_color=C["card"], border_width=1, border_color=C["border"],
                         corner_radius=12)
        self.clip = clip
        self._on_favorite = on_favorite
        self.grid_columnconfigure(1, weight=1)

        self.check = ctk.CTkCheckBox(
            self, text="", width=24, checkbox_width=18, checkbox_height=18, corner_radius=5,
            border_width=2, fg_color=C["accent"], hover_color=C["accent_hover"],
            border_color=C["subtle"], checkmark_color=C["accent_text"],
            command=lambda: on_check(clip.id, bool(self.check.get())))
        if checked:
            self.check.select()
        self.check.grid(row=0, column=0, rowspan=2, padx=(14, 2), pady=14, sticky="n")

        self.preview = label(self, utils.make_preview(clip.content), 13, wraplength=wraplength)
        self.preview.grid(row=0, column=1, sticky="w", padx=(8, 6), pady=(12, 0))
        self.meta = label(self, "", 11, color="subtle")
        self.meta.grid(row=1, column=1, sticky="w", padx=(8, 6), pady=(3, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=(4, 8))
        self.star = icon_button(actions, "star", lambda: on_favorite(clip.id))
        self.star.grid(row=0, column=0)
        icon_button(actions, "copy", lambda: on_copy(self.clip)).grid(row=0, column=1)
        icon_button(actions, "trash", lambda: on_delete(clip.id), color="danger").grid(row=0, column=2)

        for widget in (self, self.preview, self.meta):
            widget.bind("<Button-1>", lambda _e: on_select(clip.id))
        self._render_meta()
        self.set_active(active)

    def _render_meta(self) -> None:
        c = self.clip
        stats = f"{utils.format_timestamp(c.created_at)}  ·  {utils.plural(c.char_count, 'char')}"
        self.meta.configure(text=stats)
        self.star.configure(image=icon("star_fill" if c.favorite else "star", 18,
                                       "star" if c.favorite else "muted"))

    def set_favorite(self, favorite: bool) -> None:
        self.clip = dataclasses.replace(self.clip, favorite=favorite)
        self._render_meta()

    def set_active(self, active: bool) -> None:
        self.configure(border_color=C["accent"] if active else C["border"],
                       fg_color=C["card_hover"] if active else C["card"])

    def set_wrap(self, pixels: int) -> None:
        self.preview.configure(wraplength=pixels)


class PreviewPane(ctk.CTkFrame):
    """Full text, timestamps and actions for the selected clip."""

    def __init__(self, master, on_copy, on_favorite, on_delete) -> None:
        super().__init__(master, fg_color=C["card"], border_width=1, border_color=C["border"],
                         corner_radius=theme.RADIUS, width=PREVIEW_WIDTH)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.clip: Optional[Clip] = None

        self.empty = EmptyState(self, "clipboard", T.SELECT_A_CLIP,
                                "Pick a clip from the list to see its full text.", wraplength=240)
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(self.content, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 0))
        head.grid_columnconfigure(0, weight=1)
        label(head, "Preview", 15, "bold").grid(row=0, column=0, sticky="w")
        self.fav_badge = ctk.CTkLabel(head, text="", image=icon("star_fill", 16, "star"))
        self.fav_badge.grid(row=0, column=1)

        self.meta = label(self.content, "", 11, color="muted", wraplength=PREVIEW_WIDTH - 40)
        self.meta.grid(row=1, column=0, sticky="w", padx=18, pady=(4, 10))

        self.text = ctk.CTkTextbox(
            self.content, wrap="word", font=theme.mono(12), fg_color=C["input"],
            text_color=C["text"], border_width=1, border_color=C["border"], corner_radius=10,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        self.text.grid(row=2, column=0, sticky="nsew", padx=18)

        actions = ctk.CTkFrame(self.content, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=18, pady=16)
        actions.grid_columnconfigure((0, 1), weight=1)
        self.copy_btn = button(actions, "Copy", lambda: self.clip and on_copy(self.clip), "primary",
                               "copy", width=100)
        self.copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.fav_btn = button(actions, "Favorite", lambda: self.clip and on_favorite(self.clip.id),
                              "secondary", "star", width=100)
        self.fav_btn.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        icon_button(actions, "trash", lambda: self.clip and on_delete(self.clip.id), color="danger",
                    size=38, border_width=1, border_color=C["danger_soft"],
                    fg_color=C["danger_soft"], hover_color=C["danger_soft"]).grid(row=0, column=2)
        self.show(None)

    def show(self, clip: Optional[Clip]) -> None:
        self.clip = clip
        if clip is None:
            self.content.grid_remove()
            self.empty.grid(row=0, column=0, sticky="nsew")
            return
        self.empty.grid_remove()
        self.content.grid(row=0, column=0, sticky="nsew")
        chars, words, lines = utils.text_stats(clip.content)
        self.meta.configure(text=f"{utils.format_timestamp(clip.created_at)}\n"
                                 f"{chars:,} chars  ·  {words:,} words  ·  {lines:,} lines")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", utils.normalize_newlines(clip.content))
        self.text.configure(state="disabled")
        self._sync_favorite(clip.favorite)

    def set_favorite(self, favorite: bool) -> None:
        if self.clip is not None:
            self.clip = dataclasses.replace(self.clip, favorite=favorite)
            self._sync_favorite(favorite)

    def _sync_favorite(self, favorite: bool) -> None:
        if favorite:
            self.fav_badge.grid()
            self.fav_btn.configure(text="  Unfavorite", image=icon("star_fill", 17, "star"))
        else:
            self.fav_badge.grid_remove()
            self.fav_btn.configure(text="  Favorite", image=icon("star", 17, "text"))


class ClipListPage(Page):
    """Shared implementation for the History and Favorites pages."""

    def __init__(self, master, app, *, favorites_only: bool, caption: str, title: str,
                 description: str, empty_title: str, empty_message: str) -> None:
        super().__init__(master, app)
        self.favorites_only = favorites_only
        self.empty_title, self.empty_message = empty_title, empty_message
        self.query = ""
        self.sort_key = "newest"
        self.page_size = PAGE_SIZE
        self.selected: set[int] = set()
        self.active_id: Optional[int] = None
        self.rows: dict[int, ClipRow] = {}
        self._clips: list[Clip] = []
        self._total = 0
        self._resize_job = None
        self.grid_rowconfigure(3, weight=1)

        header = page_header(self, caption, title, description)
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, 14))
        self.count_label = label(header.actions, "", 12, color="muted")
        self.count_label.grid(row=0, column=0)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, 12))
        toolbar.grid_columnconfigure(0, weight=1)
        self.search = SearchBar(toolbar, T.SEARCH_PLACEHOLDER, on_change=self._on_search)
        self.search.grid(row=0, column=0, sticky="ew")
        self.sort_menu = option_menu(toolbar, SORT_OPTIONS.keys(), self._on_sort, width=170)
        self.sort_menu.grid(row=0, column=1, padx=(10, 0))

        # bulk-action bar (only visible while something is ticked)
        self.bulk = ctk.CTkFrame(self, fg_color=C["accent_soft"], corner_radius=12)
        self.bulk.grid(row=2, column=0, sticky="ew", padx=theme.PAD, pady=(0, 12))
        self.bulk.grid_columnconfigure(1, weight=1)
        self.bulk_label = label(self.bulk, "", 13, "bold", "accent")
        self.bulk_label.grid(row=0, column=0, padx=16, pady=8)
        button(self.bulk, "Select all shown", self.select_all, "ghost", width=130, height=32,
               text_color=C["accent"]).grid(row=0, column=2, padx=4, pady=6)
        button(self.bulk, "Clear", self.clear_selection, "ghost", width=70, height=32,
               text_color=C["accent"]).grid(row=0, column=3, padx=4, pady=6)
        button(self.bulk, "Delete selected", self.delete_selected, "danger", "trash",
               width=150, height=32).grid(row=0, column=4, padx=(4, 10), pady=6)
        self.bulk.grid_remove()

        # body: list + preview
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=3, column=0, sticky="nsew", padx=theme.PAD, pady=(0, theme.PAD))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, minsize=PREVIEW_WIDTH)
        self.body.grid_rowconfigure(0, weight=1)
        self.list = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        self.list.grid(row=0, column=0, sticky="nsew")
        self.list.grid_columnconfigure(0, weight=1)
        self.preview = PreviewPane(self.body, self.copy_clip, self.toggle_favorite, self.delete_one)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(theme.GAP, 0))
        self.body.bind("<Configure>", self._on_resize)

    # ---------------------------------------------------------- lifecycle
    def on_show(self, search: Optional[str] = None, select: Optional[int] = None, **kwargs) -> None:
        if search is not None:
            self.search.set(search)
            self.query = search
        if select is not None:
            self.active_id = select
        self.page_size = PAGE_SIZE
        self.refresh()

    def refresh(self) -> None:
        db = self.app.db
        scroll = self._scroll_position()
        self._clips = db.get_clips(self.query, self.sort_key, self.favorites_only, limit=self.page_size)
        self._total = db.count_clips(self.query, self.favorites_only)
        visible = {c.id for c in self._clips}
        self.selected &= visible
        if self.active_id not in visible:
            self.active_id = self._clips[0].id if self._clips else None
        self._rebuild()
        self._sync_bulk()
        shown = f"{len(self._clips):,} of {self._total:,}" if self._total > len(self._clips) else f"{self._total:,}"
        self.count_label.configure(text=f"{shown} clip{'s' if self._total != 1 else ''}")
        active = next((c for c in self._clips if c.id == self.active_id), None)
        self.preview.show(active)
        self._restore_scroll(scroll)

    # ------------------------------------------------------------ building
    def _wraplength(self) -> int:
        return max(180, self.body.winfo_width() - PREVIEW_WIDTH - theme.GAP - 200)

    def _rebuild(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        self.rows.clear()
        if not self._clips:
            searching = bool(self.query)
            title = T.EMPTY_SEARCH_TITLE if searching else self.empty_title
            message = ("Try a different word or clear the search." if searching else self.empty_message)
            if not searching and not self.favorites_only and not self.app.monitor.is_active:
                message = "Monitoring is paused - resume it from the sidebar to start recording."
            EmptyState(self.list, "search" if searching else "clipboard", title, message).grid(
                row=0, column=0, sticky="ew")
            return
        wrap = self._wraplength()
        for index, clip in enumerate(self._clips):
            row = ClipRow(
                self.list, clip, checked=clip.id in self.selected, active=clip.id == self.active_id,
                on_select=self.select, on_check=self._on_check, on_copy=self.copy_clip,
                on_favorite=self.toggle_favorite, on_delete=self.delete_one, wraplength=wrap)
            row.grid(row=index, column=0, sticky="ew", pady=(0, 8), padx=(0, 6))
            self.rows[clip.id] = row
        remaining = self._total - len(self._clips)
        if remaining > 0:
            button(self.list, f"Show more ({remaining:,} remaining)", self._show_more, "secondary",
                   width=240).grid(row=len(self._clips), column=0, pady=(4, 8))

    def _show_more(self) -> None:
        self.page_size += PAGE_SIZE
        self.refresh()

    def _on_resize(self, _event=None) -> None:
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._apply_resize)

    def _apply_resize(self) -> None:
        self._resize_job = None
        wrap = self._wraplength()
        for row in self.rows.values():
            row.set_wrap(wrap)

    def _scroll_position(self) -> float:
        try:
            return self.list._parent_canvas.yview()[0]
        except Exception:
            return 0.0

    def _restore_scroll(self, position: float) -> None:
        try:
            self.update_idletasks()
            self.list._parent_canvas.yview_moveto(position)
        except Exception:
            pass

    # ---------------------------------------------------------- search/sort
    def _on_search(self, text: str) -> None:
        self.query = text
        self.page_size = PAGE_SIZE
        self.refresh()

    def _on_sort(self, choice: str) -> None:
        self.sort_key = SORT_OPTIONS.get(choice, "newest")
        self.page_size = PAGE_SIZE
        self.refresh()

    # ------------------------------------------------------------ selection
    def select(self, clip_id: int) -> None:
        previous = self.rows.get(self.active_id)
        if previous is not None:
            previous.set_active(False)
        self.active_id = clip_id
        row = self.rows.get(clip_id)
        if row is not None:
            row.set_active(True)
            self.preview.show(row.clip)

    def _on_check(self, clip_id: int, checked: bool) -> None:
        (self.selected.add if checked else self.selected.discard)(clip_id)
        self._sync_bulk()

    def select_all(self) -> None:
        self.selected = {c.id for c in self._clips}
        for cid, row in self.rows.items():
            row.check.select()
        self._sync_bulk()

    def clear_selection(self) -> None:
        self.selected.clear()
        for row in self.rows.values():
            row.check.deselect()
        self._sync_bulk()

    def _sync_bulk(self) -> None:
        if self.selected:
            n = len(self.selected)
            self.bulk_label.configure(text=f"{n:,} selected")
            self.bulk.grid()
        else:
            self.bulk.grid_remove()

    # -------------------------------------------------------------- actions
    def copy_clip(self, clip: Clip) -> None:
        self.app.copy_text(clip.content)

    def toggle_favorite(self, clip_id: int) -> None:
        state = self.app.toggle_favorite(clip_id)
        if state is None:
            self.refresh()
            return
        if self.favorites_only and not state:
            self.refresh()            # no longer belongs on this page
            return
        row = self.rows.get(clip_id)
        if row is not None:
            row.set_favorite(state)
        if self.active_id == clip_id:
            self.preview.set_favorite(state)

    def delete_one(self, clip_id: int) -> None:
        confirmed, _ = self.app.ask_confirm(
            title="Delete this clip?", message="It will be removed permanently. This can't be undone.",
            confirm_text="Delete", danger=True)
        if confirmed:
            self.app.delete_clips([clip_id])
            self.selected.discard(clip_id)
            self.refresh()

    def delete_selected(self) -> None:
        ids = list(self.selected)
        if not ids:
            return
        confirmed, _ = self.app.ask_confirm(
            title=f"Delete {utils.plural(len(ids), 'clip')}?",
            message="The selected clips will be removed permanently. This can't be undone.",
            confirm_text="Delete", danger=True)
        if confirmed:
            self.app.delete_clips(ids)
            self.selected.clear()
            self.refresh()


class HistoryPage(ClipListPage):
    def __init__(self, master, app) -> None:
        super().__init__(
            master, app, favorites_only=False, caption=T.CAPTION_HISTORY, title="Clipboard History",
            description="Everything you've copied, newest first.",
            empty_title=T.EMPTY_HISTORY_TITLE,
            empty_message="Copy some text anywhere and it will appear here automatically.")


class FavoritesPage(ClipListPage):
    def __init__(self, master, app) -> None:
        super().__init__(
            master, app, favorites_only=True, caption=T.CAPTION_FAVORITES, title="Favorites",
            description="Clips you starred. They're never removed by the history limit.",
            empty_title=T.EMPTY_FAVORITES_TITLE,
            empty_message="Tap the star on any clip to keep it here.")
