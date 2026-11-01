"""Built-in profiles.

Brand names here are neutral placeholders. Override them with ``--brand`` on the
CLI, or build your own ``Profile`` in code, to match your product.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Dict

from .config import Palette, Profile, Theme

GENERIC = Profile(
    key="generic",
    brand="Your Product",
    title="Confirm you're a person",
    subtitle="Complete the check below to continue.",
    button="Continue",
    success="Verified. You can continue.",
    failure="That didn't match. Here is a new challenge.",
)

EV_MOTORS = Profile(
    key="ev-motors",
    brand="Voltline Motors",
    title="Reserve your service slot",
    subtitle="One quick check before we hold Thursday 09:40 for your vehicle.",
    button="Reserve slot",
    success="Slot reserved. A confirmation is on its way.",
    failure="Not quite. Try this new code.",
    length=5,
    theme=Theme(
        page_bg="#101214",
        card_bg="#191c20",
        text="#f2f3f5",
        muted="#9aa1ab",
        border="#2c3138",
        accent="#e3262e",
        accent_text="#ffffff",
        ok="#4ade80",
        error="#ff6b6b",
        radius="4px",
        button_radius="2px",
        font="'Helvetica Neue', Carlito, FreeSans, Arial, sans-serif",
    ),
    palette=Palette(
        bg_top=(38, 42, 48),
        bg_bottom=(24, 27, 31),
        inks=((245, 245, 247), (226, 232, 240), (255, 196, 196)),
        noise=((110, 118, 128), (160, 60, 64)),
    ),
)

SEARCH_CLOUD = Profile(
    key="search-cloud",
    brand="Northfield Cloud",
    title="Check before you open the workspace",
    subtitle="Complete the check in the image. This keeps automated sign-ins out.",
    button="Open workspace",
    success="You're in. Opening your workspace…",
    failure="That wasn't right. We've drawn a new image.",
    theme=Theme(
        page_bg="#f1f3f4",
        card_bg="#ffffff",
        text="#202124",
        muted="#5f6368",
        border="#dadce0",
        accent="#1a6fe0",
        accent_text="#ffffff",
        ok="#188038",
        error="#c5221f",
        radius="12px",
        button_radius="999px",
        font="'Segoe UI', Carlito, 'Helvetica Neue', FreeSans, Arial, sans-serif",
    ),
    palette=Palette(
        bg_top=(244, 247, 252),
        bg_bottom=(226, 234, 246),
        inks=((26, 111, 224), (197, 34, 31), (24, 128, 56), (32, 33, 36)),
        noise=((176, 190, 214), (218, 160, 60)),
    ),
)

FINTECH = Profile(
    key="fintech",
    brand="Meridian Pay",
    title="Approve this transfer",
    subtitle="Complete the check to confirm that you, not a script, are sending 250.00 EUR.",
    button="Send 250.00 EUR",
    success="Transfer approved.",
    failure="Wrong answer. Here is a fresh sum.",
    kind="math",
    size=(360, 110),
    theme=Theme(
        page_bg="#0b2a2e",
        card_bg="#f7f5ef",
        text="#12282b",
        muted="#53686a",
        border="#d8d4c6",
        accent="#0b6b63",
        accent_text="#ffffff",
        ok="#0b6b63",
        error="#a3261f",
        radius="18px",
        button_radius="12px",
        font="Charter, 'Bitstream Charter', Georgia, serif",
    ),
    palette=Palette(
        bg_top=(247, 245, 239),
        bg_bottom=(231, 226, 211),
        inks=((11, 107, 99), (18, 40, 43), (120, 70, 20)),
        noise=((180, 172, 150), (120, 150, 146)),
    ),
)

HEALTHCARE = Profile(
    key="healthcare",
    brand="Clearwater Clinic",
    title="Request a callback",
    subtitle="Complete the check so we know this request comes from a person.",
    button="Request callback",
    success="Request received. We'll call within one working day.",
    failure="That didn't match. Please try the new image.",
    length=5,
    theme=Theme(
        page_bg="#e9f4f2",
        card_bg="#ffffff",
        text="#173533",
        muted="#4d6c69",
        border="#c6dedb",
        accent="#00796b",
        accent_text="#ffffff",
        ok="#2e7d32",
        error="#b3261e",
        radius="22px",
        button_radius="14px",
        font="'Trebuchet MS', Carlito, FreeSans, Arial, sans-serif",
    ),
    palette=Palette(
        bg_top=(240, 249, 247),
        bg_bottom=(214, 236, 232),
        inks=((0, 96, 88), (23, 53, 51), (90, 60, 130)),
        noise=((150, 190, 184), (190, 170, 210)),
    ),
)

RETAIL = Profile(
    key="retail",
    brand="Harbor & Pine",
    title="Complete your order",
    subtitle="Last step: complete the check to place your order.",
    button="Place order",
    success="Order placed. Thank you!",
    failure="Not a match. Try the new challenge.",
    theme=Theme(
        page_bg="#fff4e0",
        card_bg="#fffdf8",
        text="#2b1d0e",
        muted="#7a6650",
        border="#ecd9b8",
        accent="#c2410c",
        accent_text="#ffffff",
        ok="#3f7d20",
        error="#b42318",
        radius="8px",
        button_radius="8px",
        font="Georgia, Charter, 'Bitstream Charter', serif",
    ),
    palette=Palette(
        bg_top=(255, 250, 238),
        bg_bottom=(247, 229, 196),
        inks=((194, 65, 12), (43, 29, 14), (22, 101, 52)),
        noise=((214, 190, 150), (200, 120, 80)),
    ),
)

PROFILES: Dict[str, Profile] = {
    p.key: p for p in (GENERIC, EV_MOTORS, SEARCH_CLOUD, FINTECH, HEALTHCARE, RETAIL)
}


def get_profile(key: str, brand: str | None = None) -> Profile:
    try:
        profile = PROFILES[key]
    except KeyError:
        raise KeyError(f"Unknown profile {key!r}. Available: {', '.join(PROFILES)}") from None
    return replace(profile, brand=brand) if brand else profile
