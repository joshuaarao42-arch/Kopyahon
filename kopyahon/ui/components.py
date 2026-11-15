"""Reusable, consistently styled widgets used by every page."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from .. import assets, theme
from ..icons import icon
from ..theme import C


# ------------------------------------------------------------------ basics
def label(master, text: str = "", size: int = 13, weight: str = "normal",
          color="text", **kw) -> ctk.CTkLabel:
    kw.setdefault("text_color", C[color] if isinstance(color, str) and color in C else color)
    kw.setdefault("anchor", "w")
    kw.setdefault("justify", "left")
    kw.setdefault("font", theme.font(size, weight))
    return ctk.CTkLabel(master, text=text, **kw)


def card(master, **kw) -> ctk.CTkFrame:
    opts = dict(fg_color=C["card"], border_width=1, border_color=C["border"],
                corner_radius=theme.RADIUS)
    opts.update(kw)
    return ctk.CTkFrame(master, **opts)


def divider(master) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, height=1, fg_color=C["border"], corner_radius=0)


_BUTTON_STYLES = {
    "primary":   dict(fg_color=C["accent"], hover_color=C["accent_hover"],
                      text_color=C["accent_text"], border_width=0, icon="accent_text"),
    "secondary": dict(fg_color=C["card_alt"], hover_color=C["card_hover"], text_color=C["text"],
                      border_width=1, border_color=C["border"], icon="text"),
    "ghost":     dict(fg_color="transparent", hover_color=C["card_hover"],
                      text_color=C["muted"], border_width=0, icon="muted"),
    "danger":    dict(fg_color=C["danger"], hover_color=C["danger_hover"],
                      text_color=C["danger_text"], border_width=0, icon="danger_text"),
    "danger_soft": dict(fg_color=C["danger_soft"], hover_color=C["danger_soft"],
                        text_color=C["danger"], border_width=1, border_color=C["danger_soft"],
                        icon="danger"),
}


def button(master, text: str, command: Optional[Callable] = None, kind: str = "primary",
           icon_name: Optional[str] = None, width: int = 130, height: int = 38, **kw) -> ctk.CTkButton:
    style = dict(_BUTTON_STYLES[kind])
    icon_color = style.pop("icon")
    opts = {**style, **kw}
    if icon_name:
        opts["image"] = icon(icon_name, 17, icon_color)
        opts.setdefault("compound", "left")
        text = "  " + text
    return ctk.CTkButton(master, text=text, command=command, width=width, height=height,
                         corner_radius=theme.RADIUS_SM,
                         font=theme.font(13, "bold" if kind in ("primary", "danger") else "normal"),
                         **opts)


def icon_button(master, name: str, command: Optional[Callable] = None, color="muted",
                size: int = 34, **kw) -> ctk.CTkButton:
    opts = dict(fg_color="transparent", hover_color=C["card_hover"], corner_radius=9)
    opts.update(kw)
    return ctk.CTkButton(master, text="", image=icon(name, 18, color), width=size, height=size,
                         command=command, **opts)


def option_menu(master, values, command=None, width: int = 190, **kw) -> ctk.CTkOptionMenu:
    return ctk.CTkOptionMenu(
        master, values=list(values), command=command, width=width, height=38,
        corner_radius=theme.RADIUS_SM, fg_color=C["card_alt"], button_color=C["border"],
        button_hover_color=C["accent_mid"], text_color=C["text"], dropdown_fg_color=C["card"],
        dropdown_hover_color=C["card_hover"], dropdown_text_color=C["text"],
        font=theme.font(13), dropdown_font=theme.font(13), anchor="w", **kw)


def switch(master, command=None, **kw) -> ctk.CTkSwitch:
    return ctk.CTkSwitch(master, text="", command=command, width=48, progress_color=C["accent"],
                         fg_color=C["border"], button_color=("#FFFFFF", "#E7EEF8"),
                         button_hover_color=("#F1F5F9", "#FFFFFF"), **kw)


def page_header(master, caption: str, title: str, description: Optional[str] = None) -> ctk.CTkFrame:
    """Caption (Cebuano) + title on the left, an ``actions`` frame on the right."""
    frame = ctk.CTkFrame(master, fg_color="transparent")
    frame.grid_columnconfigure(0, weight=1)
    text = ctk.CTkFrame(frame, fg_color="transparent")
    text.grid(row=0, column=0, sticky="w")
    label(text, caption.upper(), 11, "bold", "accent").grid(row=0, column=0, sticky="w")
    label(text, title, 26, "bold").grid(row=1, column=0, sticky="w", pady=(2, 0))
    if description:
        label(text, description, 13, color="muted").grid(row=2, column=0, sticky="w", pady=(2, 0))
    frame.actions = ctk.CTkFrame(frame, fg_color="transparent")
    frame.actions.grid(row=0, column=1, sticky="e")
    return frame


# ------------------------------------------------------------ composite
class SearchBar(ctk.CTkFrame):
    """Rounded search field with a clear button and debounced change callback."""

    def __init__(self, master, placeholder: str, on_change: Optional[Callable[[str], None]] = None,
                 on_submit: Optional[Callable[[str], None]] = None, height: int = 42) -> None:
        super().__init__(master, fg_color=C["input"], border_width=1, border_color=C["border"],
                         corner_radius=12, height=height)
        self._on_change, self._on_submit = on_change, on_submit
        self._job = None
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="", image=icon("search", 18, "subtle"), width=34).grid(
            row=0, column=0, padx=(8, 0))
        # NB: no textvariable - CTkEntry placeholders don't work together with one.
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, border_width=0,
                                  fg_color="transparent", height=height - 6, font=theme.font(13),
                                  text_color=C["text"], placeholder_text_color=C["subtle"])
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 4), pady=2)
        self.clear_btn = icon_button(self, "close", self.clear, color="subtle", size=28)
        self.clear_btn.grid(row=0, column=2, padx=(0, 6))
        self.clear_btn.grid_remove()
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Return>", self._submit)

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, text: str, notify: bool = False) -> None:
        self.entry.delete(0, "end")
        if text:
            self.entry.insert(0, text)
        self._sync_clear()
        if notify and self._on_change:
            self._on_change(self.get())

    def clear(self) -> None:
        self.set("", notify=True)

    def focus(self) -> None:
        self.entry.focus_set()

    def _sync_clear(self) -> None:
        if self.get():
            self.clear_btn.grid()
        else:
            self.clear_btn.grid_remove()

    def _on_key(self, event=None) -> None:
        self._sync_clear()
        if getattr(event, "keysym", "") == "Return":
            return
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(180, self._fire_change)

    def _fire_change(self) -> None:
        self._job = None
        if self._on_change:
            self._on_change(self.get())

    def _submit(self, _event=None) -> None:
        if self._on_submit:
            self._on_submit(self.get())


class StatusPill(ctk.CTkFrame):
    """Status indicator for active or paused monitoring."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color=C["card"], border_width=1, border_color=C["border"],
                         corner_radius=20, height=34)
        self.dot = label(self, "●", 11, color="success", width=14)
        self.dot.grid(row=0, column=0, padx=(14, 4), pady=6)
        self.text = label(self, "", 12, "bold", "text")
        self.text.grid(row=0, column=1, padx=(0, 14), pady=6)

    def set(self, active: bool) -> None:
        from .. import strings as T

        self.dot.configure(text_color=C["success"] if active else C["warning"])
        self.text.configure(text=T.STATUS_WATCHING if active else T.STATUS_PAUSED)


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, icon_name: str) -> None:
        super().__init__(master, fg_color=C["card"], border_width=1, border_color=C["border"],
                         corner_radius=theme.RADIUS)
        self.grid_columnconfigure(0, weight=1)
        label(self, title, 12, "bold", "muted").grid(row=0, column=0, sticky="w", padx=20, pady=(18, 0))
        self.value = label(self, "0", 34, "bold", "text")
        self.value.grid(row=1, column=0, sticky="w", padx=20, pady=(2, 18))
        badge = ctk.CTkFrame(self, width=44, height=44, corner_radius=12, fg_color=C["accent_soft"])
        badge.grid(row=0, column=1, rowspan=2, padx=20, sticky="e")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text="", image=icon(icon_name, 22, "accent")).place(relx=0.5, rely=0.5, anchor="center")

    def set(self, value: int) -> None:
        self.value.configure(text=f"{value:,}")


class EmptyState(ctk.CTkFrame):
    def __init__(self, master, icon_name: str, title: str, message: str,
                 action_text: Optional[str] = None, action: Optional[Callable] = None,
                 wraplength: int = 320) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        badge = ctk.CTkFrame(self, width=64, height=64, corner_radius=20, fg_color=C["accent_soft"])
        badge.grid(row=0, column=0, pady=(36, 14))
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text="", image=icon(icon_name, 28, "accent")).place(relx=0.5, rely=0.5, anchor="center")
        label(self, title, 17, "bold", anchor="center", justify="center").grid(row=1, column=0)
        label(self, message, 13, color="muted", anchor="center", justify="center",
              wraplength=wraplength).grid(row=2, column=0, pady=(6, 0))
        if action_text and action:
            button(self, action_text, action, "primary", width=170).grid(row=3, column=0, pady=(18, 0))


# ---------------------------------------------------------------- toast
class Toast(ctk.CTkFrame):
    """A single, self-dismissing notification anchored to the window's bottom-right."""

    _COLORS = {"info": "accent", "success": "success", "error": "danger", "warning": "warning"}
    _ICONS = {"info": "check", "success": "check", "error": "close", "warning": "pause"}

    def __init__(self, master) -> None:
        super().__init__(master, fg_color=C["card"], border_width=2, border_color=C["accent"],
                         corner_radius=14)
        self._job = None
        self.icon_label = ctk.CTkLabel(self, text="", image=icon("check", 18, "accent"), width=30)
        self.icon_label.grid(row=0, column=0, padx=(14, 4), pady=12)
        self.text = label(self, "", 13, "bold", wraplength=340)
        self.text.grid(row=0, column=1, padx=(0, 18), pady=12)

    def show(self, message: str, kind: str = "info", duration_ms: int = 2600) -> None:
        color = self._COLORS.get(kind, "accent")
        self.configure(border_color=C[color])
        self.icon_label.configure(image=icon(self._ICONS.get(kind, "check"), 18, color))
        self.text.configure(text=message)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-24)
        self.tkraise()
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(duration_ms, self.hide)

    def hide(self) -> None:
        self._job = None
        self.place_forget()


# -------------------------------------------------------------- dialogs
def center_on(window, parent, width: int, height: int) -> None:
    try:
        parent.update_idletasks()
        scale = window._get_window_scaling()
        x = parent.winfo_rootx() + (parent.winfo_width() - int(width * scale)) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - int(height * scale)) // 3
        window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
    except Exception:
        window.geometry(f"{width}x{height}")


class _ModalDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, width: int, height: int) -> None:
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.transient(parent)
        center_on(self, parent, width, height)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda _e: self.cancel())
        # CustomTkinter overrides toplevel icons shortly after creation on Windows.
        self.after(250, lambda: assets.apply_window_icon(self))
        self.after(120, self._grab)

    def _grab(self) -> None:
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def cancel(self) -> None:
        self.destroy()


class ConfirmDialog(_ModalDialog):
    def __init__(self, parent, title: str, message: str, confirm_text: str = "Confirm",
                 cancel_text: str = "Cancel", danger: bool = False,
                 checkbox_text: Optional[str] = None, checkbox_default: bool = True) -> None:
        height = 214 + (34 if checkbox_text else 0)
        super().__init__(parent, title, 440, height)
        self.result = False
        self.checked = checkbox_default
        body = card(self)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(0, weight=1)
        label(body, title, 17, "bold").grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))
        label(body, message, 13, color="muted", wraplength=370).grid(row=1, column=0, sticky="w", padx=22)
        row = 2
        self._checkbox = None
        if checkbox_text:
            self._checkbox = ctk.CTkCheckBox(
                body, text=checkbox_text, font=theme.font(13), text_color=C["text"],
                fg_color=C["accent"], hover_color=C["accent_hover"], border_color=C["subtle"],
                checkmark_color=C["accent_text"], corner_radius=5)
            if checkbox_default:
                self._checkbox.select()
            self._checkbox.grid(row=row, column=0, sticky="w", padx=22, pady=(12, 0))
            row += 1
        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=row, column=0, sticky="e", padx=22, pady=(18, 18))
        button(buttons, cancel_text, self.cancel, "secondary", width=100).grid(row=0, column=0, padx=(0, 10))
        button(buttons, confirm_text, self._confirm, "danger" if danger else "primary", width=120).grid(row=0, column=1)

    def _confirm(self) -> None:
        self.result = True
        if self._checkbox is not None:
            self.checked = bool(self._checkbox.get())
        self.destroy()


def ask_confirm(parent, **kwargs) -> tuple[bool, bool]:
    """Show a modal confirmation. Returns ``(confirmed, checkbox_ticked)``."""
    dialog = ConfirmDialog(parent, **kwargs)
    parent.wait_window(dialog)
    return dialog.result, dialog.checked
