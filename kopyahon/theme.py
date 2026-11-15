"""Design tokens: colours, spacing and fonts.

Every colour is a ``(light, dark)`` tuple, which CustomTkinter resolves live,
so switching theme restyles the whole app without rebuilding any widget.
Never hard-code colours in UI modules - add a token here instead.
"""
from __future__ import annotations

from functools import lru_cache

import customtkinter as ctk

C: dict[str, tuple[str, str]] = {
    # surfaces                    light       dark (deep navy / charcoal)
    "bg":            ("#EEF2F7", "#0A111D"),
    "sidebar":       ("#FFFFFF", "#080E18"),
    "card":          ("#FFFFFF", "#101A2B"),
    "card_alt":      ("#F4F7FB", "#0C1524"),
    "card_hover":    ("#E9EFF6", "#17253C"),
    "input":         ("#F4F7FB", "#0C1524"),
    "border":        ("#D9E2ED", "#1C2A41"),
    # text
    "text":          ("#0F1B2D", "#E7EEF8"),
    "muted":         ("#566882", "#8797B1"),
    "subtle":        ("#8696AD", "#5F6F89"),
    # teal accent
    "accent":        ("#0D9488", "#2DD4BF"),
    "accent_hover":  ("#0F766E", "#5EEAD4"),
    "accent_text":   ("#FFFFFF", "#04211D"),   # text/icons on a solid accent fill
    "accent_soft":   ("#D7F2EE", "#0F2E36"),
    "accent_mid":    ("#B5E6DF", "#16505A"),
    # feedback
    "danger":        ("#DC2626", "#F87171"),
    "danger_hover":  ("#B91C1C", "#FCA5A5"),
    "danger_soft":   ("#FDE8E8", "#34161E"),
    "danger_text":   ("#FFFFFF", "#2A0A0A"),
    "star":          ("#D99A00", "#FBBF24"),
    "success":       ("#16A34A", "#4ADE80"),
    "warning":       ("#D97706", "#FBBF24"),
}

RADIUS = 14
RADIUS_SM = 10
PAD = 28        # page margin
GAP = 16        # gap between cards

_FONT_CANDIDATES = ("Segoe UI Variable Display", "Segoe UI", "Inter", "SF Pro Text",
                    "Helvetica Neue", "Ubuntu", "Noto Sans", "DejaVu Sans")
_MONO_CANDIDATES = ("Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", "Courier New")

_family = None
_mono_family = None


def init_fonts(root) -> None:
    """Pick the best installed fonts. Call once, after the root window exists."""
    global _family, _mono_family
    import tkinter.font as tkfont

    try:
        available = set(tkfont.families(root))
    except Exception:
        available = set()
    _family = next((f for f in _FONT_CANDIDATES if f in available), None)
    _mono_family = next((f for f in _MONO_CANDIDATES if f in available), None)
    _font.cache_clear()
    _mono.cache_clear()


@lru_cache(maxsize=None)
def _font(size: int, weight: str):
    return ctk.CTkFont(family=_family, size=size, weight=weight)


@lru_cache(maxsize=None)
def _mono(size: int):
    return ctk.CTkFont(family=_mono_family or _family, size=size)


def font(size: int = 13, weight: str = "normal"):
    return _font(size, weight)


def mono(size: int = 12):
    return _mono(size)


def hex_pair(color) -> tuple[str, str]:
    """Resolve a token name / tuple / hex string into a (light, dark) pair."""
    value = C[color] if isinstance(color, str) and color in C else color
    if isinstance(value, str):
        return value, value
    return value[0], value[1]
