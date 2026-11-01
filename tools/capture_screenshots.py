"""Drive the real web UI in headless Chromium and save screenshots.

Needs the optional dev dependency:  pip install playwright && playwright install chromium
Usage:  python tools/capture_screenshots.py [output_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from humancheck import ChallengeService, Verifier  # noqa: E402
from humancheck.challenges import ChallengeSpec, math_spec  # noqa: E402
from humancheck.profiles import PROFILES  # noqa: E402
from humancheck.server import create_server, serve_in_thread  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
FLOW_PROFILES = ("ev-motors", "search-cloud")

last = {"answer": ""}


def spec_factory(kind: str, length: int) -> ChallengeSpec:
    spec = math_spec() if kind == "math" else ChallengeSpec(
        "text", "K7M4QXH9"[:length], "K7M4QXH9"[:length], "Type the characters you see")
    last["answer"] = spec.answer
    return spec


def ready(page) -> None:
    page.wait_for_function(
        "() => { const i = document.getElementById('captcha');"
        " return i.complete && i.naturalWidth > 0 && !i.classList.contains('loading'); }")
    page.wait_for_timeout(150)


def main() -> None:
    server = create_server("127.0.0.1", 0, ChallengeService(Verifier(), spec_factory))
    base = f"http://127.0.0.1:{server.server_address[1]}"
    serve_in_thread(server)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 760, "height": 640}, device_scale_factor=2)
        page = ctx.new_page()

        for key in PROFILES:
            page.goto(f"{base}/?profile={key}&embed=1")
            ready(page)
            page.screenshot(path=OUT / f"{key}.png")

            if key in FLOW_PROFILES:
                page.fill("#answer", "WRONG")
                page.click("#submit")
                page.wait_for_selector("#status.error")
                page.wait_for_timeout(500)          # let the shake settle
                ready(page)
                page.screenshot(path=OUT / f"{key}-wrong-answer.png")

                page.fill("#answer", last["answer"])
                page.click("#submit")
                page.wait_for_selector("#status.ok")
                page.screenshot(path=OUT / f"{key}-verified.png")

        # Demo page with the profile/challenge switcher visible, math variant.
        page.goto(f"{base}/?profile=search-cloud&kind=math")
        ready(page)
        page.screenshot(path=OUT / "demo-switcher-math.png")

        mobile = browser.new_context(viewport={"width": 390, "height": 760}, device_scale_factor=2,
                                     is_mobile=True, has_touch=True)
        mp = mobile.new_page()
        mp.goto(f"{base}/?profile=ev-motors&embed=1")
        ready(mp)
        mp.screenshot(path=OUT / "mobile-ev-motors.png")
        browser.close()
    server.shutdown()

    # Overview montage of all initial profile screens.
    keys = list(PROFILES)
    thumbs = [Image.open(OUT / f"{k}.png").convert("RGB") for k in keys]
    tw, th = thumbs[0].size
    scale, gap = 0.5, 24
    w, h = int(tw * scale), int(th * scale)
    cols = 3
    rows = -(-len(thumbs) // cols)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), (24, 26, 30))
    for i, t in enumerate(thumbs):
        sheet.paste(t.resize((w, h), Image.LANCZOS), (gap + (i % cols) * (w + gap), gap + (i // cols) * (h + gap)))
    sheet.save(OUT / "overview.png", optimize=True)
    print("saved", len(list(OUT.glob("*.png"))), "images to", OUT)


if __name__ == "__main__":
    main()
