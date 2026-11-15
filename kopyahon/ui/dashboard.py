"""Dashboard: greeting, search, statistics, recent activity and quick actions."""
from __future__ import annotations

import customtkinter as ctk

from .. import strings as T, theme, utils
from ..constants import RECENT_LIMIT
from ..icons import icon
from ..theme import C
from .components import (EmptyState, SearchBar, StatCard, StatusPill, button, card,
                         icon_button, label)
from .page import Page


class DashboardPage(Page):
    def __init__(self, master, app) -> None:
        super().__init__(master, app)
        self.grid_rowconfigure(3, weight=1)

        # ---- header: greeting + monitoring pill
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD, 14))
        head.grid_columnconfigure(0, weight=1)
        label(head, T.CAPTION_DASHBOARD.upper(), 11, "bold", "accent").grid(row=0, column=0, sticky="w")
        self.greeting = label(head, "", 26, "bold")
        self.greeting.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.subtitle = label(head, "", 13, color="muted")
        self.subtitle.grid(row=2, column=0, sticky="w", pady=(2, 0))
        self.pill = StatusPill(head)
        self.pill.grid(row=0, column=1, rowspan=3, sticky="e")

        # ---- search
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.grid(row=1, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.GAP))
        search_row.grid_columnconfigure(0, weight=1)
        self.search = SearchBar(search_row, T.SEARCH_PLACEHOLDER, on_submit=self._search, height=46)
        self.search.grid(row=0, column=0, sticky="ew")
        button(search_row, "Search", lambda: self._search(self.search.get()), "primary",
               "search", width=120, height=46).grid(row=0, column=1, padx=(10, 0))

        # ---- statistics
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=theme.PAD, pady=(0, theme.GAP))
        for col in range(3):
            stats.grid_columnconfigure(col, weight=1, uniform="stat")
        self.stat_total = StatCard(stats, "Total clips", "clipboard")
        self.stat_today = StatCard(stats, "Today's clips", "history")
        self.stat_favs = StatCard(stats, "Favorites", "star")
        for col, widget in enumerate((self.stat_total, self.stat_today, self.stat_favs)):
            widget.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else theme.GAP // 2,
                                                              0 if col == 2 else theme.GAP // 2))

        # ---- recent activity + quick actions
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="nsew", padx=theme.PAD, pady=(0, theme.PAD))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=1, minsize=270)
        bottom.grid_rowconfigure(0, weight=1)

        recent = card(bottom)
        recent.grid(row=0, column=0, sticky="nsew", padx=(0, theme.GAP // 2))
        recent.grid_columnconfigure(0, weight=1)
        recent.grid_rowconfigure(1, weight=1)
        rhead = ctk.CTkFrame(recent, fg_color="transparent")
        rhead.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        rhead.grid_columnconfigure(0, weight=1)
        label(rhead, "Recent activity", 15, "bold").grid(row=0, column=0, sticky="w")
        button(rhead, "View all", lambda: app.show_page("history"), "ghost", width=80, height=30).grid(row=0, column=1)
        self.recent_list = ctk.CTkScrollableFrame(
            recent, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["subtle"])
        self.recent_list.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(0, 10))
        self.recent_list.grid_columnconfigure(0, weight=1)

        quick = card(bottom)
        quick.grid(row=0, column=1, sticky="nsew", padx=(theme.GAP // 2, 0))
        quick.grid_columnconfigure(0, weight=1)
        qhead = ctk.CTkFrame(quick, fg_color="transparent")
        qhead.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(qhead, text="", image=icon("bolt", 18, "accent")).grid(row=0, column=0, padx=(0, 8))
        label(qhead, "Quick actions", 15, "bold").grid(row=0, column=1)
        self.pause_btn = button(quick, "Pause monitoring", app.toggle_monitoring, "secondary", "pause", width=200)
        self.copy_latest_btn = button(quick, "Copy latest clip", self._copy_latest, "secondary", "copy", width=200)
        buttons = (
            self.pause_btn,
            self.copy_latest_btn,
            button(quick, "New snippet", lambda: app.show_page("snippets", new=True), "secondary", "plus", width=200),
            button(quick, "Open history", lambda: app.show_page("history"), "secondary", "history", width=200),
            button(quick, "View favorites", lambda: app.show_page("favorites"), "secondary", "star", width=200),
        )
        for i, btn in enumerate(buttons, start=1):
            btn.configure(anchor="w")
            btn.grid(row=i, column=0, sticky="ew", padx=16, pady=(0, 8))

    # ------------------------------------------------------------- actions
    def _search(self, query: str) -> None:
        self.app.show_page("history", search=query)

    def _copy_latest(self) -> None:
        clip = self.app.db.get_latest_clip()
        if clip is None:
            self.app.notify(T.EMPTY_HISTORY_TITLE, "warning")
        else:
            self.app.copy_text(clip.content)

    def _toggle_favorite(self, clip_id: int) -> None:
        self.app.toggle_favorite(clip_id)
        self.refresh()

    # ------------------------------------------------------------- refresh
    def on_show(self, **kwargs) -> None:
        self.search.set("")
        self.refresh()

    def refresh(self) -> None:
        db = self.app.db
        stats = db.stats()
        self.stat_total.set(stats["total"])
        self.stat_today.set(stats["today"])
        self.stat_favs.set(stats["favorites"])
        self.greeting.configure(text=f"{utils.greeting()}, {utils.display_name()}!")
        self.subtitle.configure(text=utils.format_long_date())
        active = self.app.monitor.is_active
        self.pill.set(active)
        if active:
            self.pause_btn.configure(text="  Pause monitoring", image=icon("pause", 17, "text"))
        else:
            self.pause_btn.configure(text="  Resume monitoring", image=icon("play", 17, "text"))
        self._render_recent()

    def _render_recent(self) -> None:
        for child in self.recent_list.winfo_children():
            child.destroy()
        clips = self.app.db.get_clips(limit=RECENT_LIMIT)
        if not clips:
            hint = ("Monitoring is paused - resume it to start recording."
                    if not self.app.monitor.is_active
                    else "Copy some text anywhere and it will show up here.")
            EmptyState(self.recent_list, "clipboard", T.EMPTY_HISTORY_TITLE, hint).grid(
                row=0, column=0, sticky="ew")
            return
        for row, clip in enumerate(clips):
            item = ctk.CTkFrame(self.recent_list, fg_color=C["card_alt"], corner_radius=12)
            item.grid(row=row, column=0, sticky="ew", pady=(0, 6), padx=(0, 4))
            item.grid_columnconfigure(0, weight=1)
            text = utils.make_preview(clip.content, max_lines=1, max_chars=90).replace("\n", " ")
            title = label(item, text, 13, wraplength=520)
            title.grid(row=0, column=0, sticky="w", padx=(14, 6), pady=(9, 0))
            meta = label(item, f"{utils.time_ago(clip.created_at)}  ·  {utils.plural(clip.char_count, 'char')}",
                         11, color="subtle")
            meta.grid(row=1, column=0, sticky="w", padx=(14, 6), pady=(0, 9))
            actions = ctk.CTkFrame(item, fg_color="transparent")
            actions.grid(row=0, column=1, rowspan=2, padx=(0, 6))
            icon_button(actions, "star_fill" if clip.favorite else "star",
                        lambda cid=clip.id: self._toggle_favorite(cid),
                        color="star" if clip.favorite else "muted").grid(row=0, column=0)
            icon_button(actions, "copy", lambda c=clip: self.app.copy_text(c.content)).grid(row=0, column=1)
            for widget in (item, title, meta):
                widget.bind("<Button-1>", lambda _e, cid=clip.id: self.app.show_page("history", select=cid))
