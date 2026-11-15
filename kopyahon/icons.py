"""Crisp vector-style icons drawn with Pillow (no icon fonts or image files).

``icon("star", 18, "accent")`` returns a cached ``CTkImage`` with a light and a
dark variant, so icons recolour automatically when the theme changes.
"""
from __future__ import annotations

import math
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw

from .theme import hex_pair

_SS = 4        # supersampling factor for smooth edges
_GRID = 24     # icons are designed on a 24 x 24 grid


class _Pen:
    def __init__(self, px: int, color: str) -> None:
        self.size = px * _SS
        self.u = self.size / _GRID
        self.color = color
        self.w = max(1, round(2 * self.u))
        self.img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _p(self, point):
        return point[0] * self.u, point[1] * self.u

    def line(self, pts, width: float | None = None) -> None:
        w = max(1, round(width * self.u)) if width else self.w
        pts = [self._p(p) for p in pts]
        self.d.line(pts, fill=self.color, width=w, joint="curve")
        r = w / 2
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=self.color)

    def rrect(self, box, radius: float = 2, fill: bool = False, clear: bool = False) -> None:
        b = [v * self.u for v in box]
        if clear:
            self.d.rounded_rectangle(b, radius=radius * self.u, fill=(0, 0, 0, 0))
        elif fill:
            self.d.rounded_rectangle(b, radius=radius * self.u, fill=self.color)
        else:
            self.d.rounded_rectangle(b, radius=radius * self.u, outline=self.color, width=self.w)

    def circle(self, cx, cy, r, fill: bool = False, clear: bool = False) -> None:
        b = ((cx - r) * self.u, (cy - r) * self.u, (cx + r) * self.u, (cy + r) * self.u)
        if clear:
            self.d.ellipse(b, fill=(0, 0, 0, 0))
        elif fill:
            self.d.ellipse(b, fill=self.color)
        else:
            self.d.ellipse(b, outline=self.color, width=self.w)

    def poly(self, pts) -> None:
        self.d.polygon([self._p(p) for p in pts], fill=self.color)


def _star_points(cx=12.0, cy=12.6, outer=9.6, inner=4.1):
    pts = []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        ang = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def _dashboard(p):
    for box in ((3, 3, 10.5, 10.5), (13.5, 3, 21, 10.5), (3, 13.5, 10.5, 21), (13.5, 13.5, 21, 21)):
        p.rrect(box, 2)


def _history(p):
    p.circle(12, 12, 9)
    p.line([(12, 7), (12, 12), (15.5, 14)])


def _star(p):
    pts = _star_points()
    p.line(pts + [pts[0]])


def _star_fill(p):
    pts = _star_points()
    p.poly(pts)
    p.line(pts + [pts[0]], width=1.2)


def _snippet(p):
    p.rrect((4.5, 3, 19.5, 21), 2.5)
    p.line([(8, 9), (16, 9)])
    p.line([(8, 13), (16, 13)])
    p.line([(8, 17), (13, 17)])


def _settings(p):
    for y in (6, 12, 18):
        p.line([(4, y), (20, y)])
    for cx, cy in ((9, 6), (15, 12), (8, 18)):
        p.circle(cx, cy, 3.6, clear=True)
        p.circle(cx, cy, 2.4, fill=True)


def _about(p):
    p.circle(12, 12, 9)
    p.circle(12, 7.8, 1.2, fill=True)
    p.line([(12, 11), (12, 16.5)])


def _copy(p):
    p.rrect((4, 4, 15, 15), 2)
    p.rrect((7.5, 7.5, 21.5, 21.5), 2.5, clear=True)
    p.rrect((9, 9, 20, 20), 2)


def _trash(p):
    p.line([(4, 7), (20, 7)])
    p.line([(9.5, 7), (9.5, 4), (14.5, 4), (14.5, 7)])
    p.line([(6, 7), (7, 20), (8, 21), (16, 21), (17, 20), (18, 7)])
    p.line([(10, 11), (10, 17)], width=1.6)
    p.line([(14, 11), (14, 17)], width=1.6)


def _search(p):
    p.circle(10.5, 10.5, 6.5)
    p.line([(15.5, 15.5), (20, 20)])


def _pause(p):
    p.rrect((6.5, 5, 10, 19), 1, fill=True)
    p.rrect((14, 5, 17.5, 19), 1, fill=True)


def _play(p):
    p.poly([(8, 5), (19, 12), (8, 19)])
    p.line([(8, 5), (19, 12), (8, 19), (8, 5)], width=1.4)


def _plus(p):
    p.line([(12, 5), (12, 19)])
    p.line([(5, 12), (19, 12)])


def _edit(p):
    p.line([(7, 17), (17, 7)], width=3.2)
    p.poly([(4, 20), (5.2, 15.2), (8.8, 18.8)])


def _check(p):
    p.line([(5, 12.5), (10, 17.5), (19, 7)])


def _close(p):
    p.line([(6, 6), (18, 18)])
    p.line([(18, 6), (6, 18)])


def _clipboard(p):
    p.rrect((5, 5, 19, 21), 2.5)
    p.rrect((9, 2.5, 15, 6.5), 1.5, fill=True)


def _bolt(p):
    p.poly([(13, 2.5), (5, 13.5), (11, 13.5), (10, 21.5), (19, 10), (13, 10)])


def _folder(p):
    pts = [(3, 6.5), (9, 6.5), (11, 8.5), (21, 8.5), (21, 19), (3, 19)]
    p.line(pts + [pts[0]])


def _sun(p):
    p.circle(12, 12, 4)
    for i in range(8):
        a = i * math.pi / 4
        p.line([(12 + 7 * math.cos(a), 12 + 7 * math.sin(a)),
                (12 + 9.5 * math.cos(a), 12 + 9.5 * math.sin(a))], width=1.8)


_DRAWERS = {
    "dashboard": _dashboard, "history": _history, "star": _star, "star_fill": _star_fill,
    "snippet": _snippet, "settings": _settings, "about": _about, "copy": _copy,
    "trash": _trash, "search": _search, "pause": _pause, "play": _play, "plus": _plus,
    "edit": _edit, "check": _check, "close": _close, "clipboard": _clipboard,
    "bolt": _bolt, "folder": _folder, "sun": _sun,
}


def render(name: str, px: int, color: str) -> Image.Image:
    pen = _Pen(px, color)
    _DRAWERS[name](pen)
    return pen.img.resize((px, px), Image.Resampling.LANCZOS)


@lru_cache(maxsize=None)
def icon(name: str, size: int = 18, color="muted") -> ctk.CTkImage:
    light, dark = hex_pair(color)
    px = size * 2          # render at 2x so it stays sharp on HiDPI screens
    return ctk.CTkImage(light_image=render(name, px, light),
                        dark_image=render(name, px, dark), size=(size, size))
