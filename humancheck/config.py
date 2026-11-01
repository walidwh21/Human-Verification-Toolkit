"""Plain data structures describing how a verification screen looks and reads."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

RGB = Tuple[int, int, int]


@dataclass(frozen=True)
class Palette:
    """Colours used when drawing the challenge image itself."""

    bg_top: RGB = (236, 240, 245)
    bg_bottom: RGB = (214, 222, 233)
    inks: Tuple[RGB, ...] = ((24, 38, 66), (44, 62, 110), (20, 84, 96))
    noise: Tuple[RGB, ...] = ((120, 132, 156), (150, 160, 180))


@dataclass(frozen=True)
class Theme:
    """Colours and shape tokens for the web UI (exposed as CSS variables)."""

    page_bg: str = "#eef1f5"
    card_bg: str = "#ffffff"
    text: str = "#18202e"
    muted: str = "#5b6678"
    border: str = "#d5dbe5"
    accent: str = "#0f766e"
    accent_text: str = "#ffffff"
    ok: str = "#15803d"
    error: str = "#b91c1c"
    radius: str = "14px"
    button_radius: str = "10px"
    font: str = "'Segoe UI', Carlito, 'Helvetica Neue', FreeSans, Arial, sans-serif"

    def as_css_vars(self) -> dict:
        return {
            "--page-bg": self.page_bg,
            "--card-bg": self.card_bg,
            "--text": self.text,
            "--muted": self.muted,
            "--border": self.border,
            "--accent": self.accent,
            "--accent-text": self.accent_text,
            "--ok": self.ok,
            "--error": self.error,
            "--radius": self.radius,
            "--button-radius": self.button_radius,
            "--font": self.font,
        }


@dataclass(frozen=True)
class Profile:
    """One use case ("action") for the verifier: copy, look, and challenge rules."""

    key: str
    brand: str
    title: str
    subtitle: str
    button: str
    success: str
    failure: str
    kind: str = "text"            # "text" or "math"
    length: int = 6               # characters for text challenges
    size: Tuple[int, int] = (300, 110)
    ttl_seconds: int = 180
    max_attempts: int = 3
    theme: Theme = field(default_factory=Theme)
    palette: Palette = field(default_factory=Palette)

    def public_dict(self) -> dict:
        """Everything the browser needs, and nothing it shouldn't have."""
        return {
            "key": self.key,
            "brand": self.brand,
            "title": self.title,
            "subtitle": self.subtitle,
            "button": self.button,
            "success": self.success,
            "failure": self.failure,
            "kind": self.kind,
            "theme": self.theme.as_css_vars(),
        }
