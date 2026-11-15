"""Logo and application icon.

The KOPYAHON mark is original artwork generated with Pillow: a teal tile
holding two stacked pages (a *kopya* - a copy) with a "K" on the front page.
Run ``python -m kopyahon.assets`` to regenerate ``assets/logo.png`` and
``assets/icon.ico``; the app also regenerates them if they are missing.
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw

from .utils import assets_dir

log = logging.getLogger(__name__)

_NAVY = (7, 18, 32, 255)
_TEAL = (45, 212, 191, 255)
_ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _gradient(size: int, top, bottom) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (size, y)], fill=color)
    return img


def generate_logo(size: int = 1024) -> Image.Image:
    s = 1024
    tile = _gradient(s, (45, 212, 191), (13, 148, 136))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((40, 40, s - 40, s - 40), radius=230, fill=255)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(tile, (0, 0), mask)

    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # back page (the "copy"), outline only
    d.rounded_rectangle((215, 165, 625, 690), radius=70, outline=(7, 18, 32, 150), width=40)
    # front page + clip
    d.rounded_rectangle((345, 285, 805, 865), radius=84, fill=_NAVY)
    d.rounded_rectangle((470, 225, 680, 345), radius=44, fill=_NAVY)
    d.rounded_rectangle((530, 255, 620, 290), radius=17, fill=_TEAL)

    def stroke(points, width):
        d.line(points, fill=_TEAL, width=width)
        r = width / 2
        for x, y in (points[0], points[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=_TEAL)

    # the "K"
    stroke([(512, 470), (512, 730)], 58)
    stroke([(512, 600), (668, 466)], 58)
    stroke([(530, 600), (668, 732)], 58)

    canvas = Image.alpha_composite(canvas, layer)
    if size != s:
        canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
    return canvas


def logo_path():
    return assets_dir() / "logo.png"


def icon_path():
    return assets_dir() / "icon.ico"


def ensure_assets(force: bool = False) -> None:
    folder = assets_dir()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if force or not logo_path().exists():
            generate_logo(512).save(logo_path())
        if force or not icon_path().exists():
            generate_logo(256).save(icon_path(), format="ICO", sizes=_ICO_SIZES)
    except OSError as exc:       # read-only install location, etc.
        log.warning("Could not write assets: %s", exc)


@lru_cache(maxsize=None)
def load_logo(size: int) -> ctk.CTkImage:
    path = logo_path()
    image = Image.open(path).convert("RGBA") if path.exists() else generate_logo(512)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


def apply_window_icon(window) -> None:
    """Set the title-bar/taskbar icon (best effort, never raises)."""
    try:
        if sys.platform.startswith("win") and icon_path().exists():
            window.iconbitmap(str(icon_path()))
        elif logo_path().exists():
            import tkinter

            photo = tkinter.PhotoImage(file=str(logo_path()))
            window.iconphoto(True, photo)
            window._kopyahon_icon = photo     # keep a reference alive
    except Exception as exc:
        log.debug("Could not set window icon: %s", exc)


if __name__ == "__main__":
    ensure_assets(force=True)
    print(f"Wrote {logo_path()} and {icon_path()}")
