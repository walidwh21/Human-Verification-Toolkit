"""Command line entry point: ``python -m humancheck <command>``."""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from PIL import Image

from .challenges import make_spec
from .profiles import PROFILES, get_profile
from .renderer import render, to_png_bytes


def _cmd_serve(args) -> int:
    from .server import create_server

    profiles = dict(PROFILES)
    if args.brand:
        profiles = {k: get_profile(k, args.brand) for k in profiles}
    server = create_server(args.host, args.port, profiles=profiles)
    first = args.profile if args.profile in profiles else next(iter(profiles))
    print(f"Serving on http://{args.host}:{args.port}/?profile={first}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


def _cmd_generate(args) -> int:
    profile = get_profile(args.profile)
    spec = make_spec(args.kind or profile.kind, profile.length)
    image = render(spec.display, profile.size, profile.palette)
    Path(args.out).write_bytes(to_png_bytes(image))
    # The answer goes to stdout only; the image carries no metadata.
    print(spec.answer)
    return 0


def _cmd_gallery(args) -> int:
    cols, pad = args.columns, 14
    tiles = []
    for i in range(args.count):
        profile = list(PROFILES.values())[i % len(PROFILES)]
        spec = make_spec(profile.kind, profile.length)
        tiles.append(render(spec.display, profile.size, profile.palette, random.Random(args.seed + i)))
    tw, th = max(t.width for t in tiles), max(t.height for t in tiles)
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad), (245, 246, 248))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + pad)))
    Path(args.out).write_bytes(to_png_bytes(sheet))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="humancheck", description="Human-verification toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("serve", help="run the demo web server")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--profile", default="generic", choices=list(PROFILES))
    s.add_argument("--brand", help="replace the brand name shown on every profile")
    s.set_defaults(func=_cmd_serve)

    g = sub.add_parser("generate", help="write one challenge image and print its answer")
    g.add_argument("--out", default="challenge.png")
    g.add_argument("--profile", default="generic", choices=list(PROFILES))
    g.add_argument("--kind", choices=("text", "math"))
    g.set_defaults(func=_cmd_generate)

    gal = sub.add_parser("gallery", help="render a contact sheet of sample challenges")
    gal.add_argument("--out", default="gallery.png")
    gal.add_argument("--count", type=int, default=12)
    gal.add_argument("--columns", type=int, default=3)
    gal.add_argument("--seed", type=int, default=7)
    gal.set_defaults(func=_cmd_gallery)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
