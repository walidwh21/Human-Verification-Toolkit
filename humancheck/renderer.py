"""Pure-Pillow challenge image renderer (no third-party captcha package needed)."""
from __future__ import annotations

import functools
import io
import math
import random
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import Palette

_FONT_CANDIDATES = (
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
    "FreeSansBold.ttf",
    "Carlito-Bold.ttf",
    "Arial Bold.ttf",
    "arialbd.ttf",
    "Helvetica.ttc",
)
_FONT_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/freefont",
    "/usr/share/fonts/truetype/crosextra",
    "/Library/Fonts",
    "/System/Library/Fonts",
    "C:/Windows/Fonts",
)


@functools.lru_cache(maxsize=64)
def load_font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
        for folder in _FONT_DIRS:
            try:
                return ImageFont.truetype(f"{folder}/{name}", size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def _gradient(w: int, h: int, top: Tuple[int, int, int], bottom: Tuple[int, int, int]) -> Image.Image:
    t = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype("uint8"), "RGB")


def _wave(layer: Image.Image, rng: random.Random, amplitude: float) -> Image.Image:
    arr = np.array(layer)
    period = rng.uniform(55, 90)
    phase = rng.uniform(0, math.tau)
    out = np.zeros_like(arr)
    for x in range(arr.shape[1]):
        shift = int(round(amplitude * math.sin(math.tau * x / period + phase)))
        if shift > 0:
            out[shift:, x] = arr[:-shift, x]
        elif shift < 0:
            out[:shift, x] = arr[-shift:, x]
        else:
            out[:, x] = arr[:, x]
    return Image.fromarray(out, "RGBA")


def _strike(draw: ImageDraw.ImageDraw, w: int, h: int, color, rng: random.Random) -> None:
    amp = rng.uniform(h * 0.08, h * 0.22)
    period = rng.uniform(w * 0.4, w * 0.9)
    phase = rng.uniform(0, math.tau)
    y0 = rng.uniform(h * 0.25, h * 0.75)
    pts = [(x, y0 + amp * math.sin(math.tau * x / period + phase)) for x in range(0, w, 4)]
    draw.line(pts, fill=color, width=2)


def render(
    text: str,
    size: Tuple[int, int] = (300, 110),
    palette: Optional[Palette] = None,
    rng: Optional[random.Random] = None,
) -> Image.Image:
    """Draw ``text`` with per-glyph rotation, a wave warp, crossing strokes and speckle."""
    palette = palette or Palette()
    rng = rng or random.Random()
    w, h = size
    pad = int(w * 0.07)

    image = _gradient(w, h, palette.bg_top, palette.bg_bottom)

    glyphs = list(text)
    visible = sum(1 for g in glyphs if g != " ")
    spaces = len(glyphs) - visible
    unit = (w - 2 * pad) / (visible + 0.6 * spaces)

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = float(pad)
    for g in glyphs:
        if g == " ":
            x += unit * 0.6
            continue
        font = load_font(int(min(h * rng.uniform(0.50, 0.60), unit * rng.uniform(1.0, 1.12))))
        tile = Image.new("RGBA", (int(unit * 1.9), h), (0, 0, 0, 0))
        d = ImageDraw.Draw(tile)
        l, t, r, b = d.textbbox((0, 0), g, font=font)
        d.text(
            ((tile.width - (r - l)) / 2 - l, (h - (b - t)) / 2 - t),
            g,
            font=font,
            fill=rng.choice(palette.inks) + (255,),
        )
        tile = tile.rotate(rng.uniform(-17, 17), resample=Image.BICUBIC)
        layer.paste(tile, (int(x + unit / 2 - tile.width / 2), rng.randint(-4, 4)), tile)
        x += unit

    layer = _wave(layer, rng, amplitude=h * 0.045)
    image.paste(layer, (0, 0), layer)

    # Speckle first, strokes on top so they cross the glyphs.
    draw = ImageDraw.Draw(image)
    for _ in range(int(w * h / 160)):
        px, py = rng.randrange(w), rng.randrange(h)
        draw.point((px, py), fill=rng.choice(palette.noise))
    for _ in range(2):
        _strike(draw, w, h, rng.choice(palette.noise + palette.inks), rng)

    return image.filter(ImageFilter.GaussianBlur(0.45))


def to_png_bytes(image: Image.Image) -> bytes:
    """Encode without any metadata."""
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
