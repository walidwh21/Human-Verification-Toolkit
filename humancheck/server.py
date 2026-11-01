"""Tiny standard-library web server that demonstrates the verifier end to end.

Endpoints
    GET  /                      demo page (``?profile=<key>&embed=1``)
    GET  /api/profiles          list of profile keys and display names
    GET  /api/profile/<key>     copy + theme for one profile
    GET  /api/challenge         ?profile=<key>&kind=text|math
    POST /api/verify            {"token": "...", "answer": "...", "profile": "<key>"}
"""
from __future__ import annotations

import base64
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

from .config import Profile
from .profiles import PROFILES
from .service import ChallengeService

STATIC = Path(__file__).parent / "static"
MAX_BODY = 4096
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'",
}


def make_handler(service: ChallengeService, profiles: Dict[str, Profile]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "HumanCheck"
        sys_version = ""

        # -- helpers -------------------------------------------------------
        def _send(self, status: int, body: bytes, ctype: str, cache: bool = False) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=300" if cache else "no-store")
            for k, v in SECURITY_HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json")

        def _profile(self, key: Optional[str]) -> Optional[Profile]:
            return profiles.get(key or next(iter(profiles)))

        def _challenge_payload(self, profile: Profile, kind: Optional[str]) -> dict:
            ch = service.create(profile, kind)
            return {
                "token": ch.token,
                "kind": ch.kind,
                "prompt": ch.prompt,
                "expires_in": ch.expires_in,
                "image": "data:image/png;base64," + base64.b64encode(ch.png).decode(),
            }

        # -- routes --------------------------------------------------------
        def do_GET(self) -> None:  # noqa: N802
            url = urlparse(self.path)
            query = parse_qs(url.query)
            first = lambda name: (query.get(name) or [None])[0]  # noqa: E731

            if url.path == "/api/profiles":
                return self._json(200, [{"key": p.key, "name": p.brand} for p in profiles.values()])
            if url.path.startswith("/api/profile/"):
                profile = self._profile(url.path.rsplit("/", 1)[-1])
                return self._json(200, profile.public_dict()) if profile else self._json(404, {"error": "unknown profile"})
            if url.path == "/api/challenge":
                profile = self._profile(first("profile"))
                kind = first("kind")
                if not profile or kind not in (None, "text", "math"):
                    return self._json(400, {"error": "bad request"})
                return self._json(200, self._challenge_payload(profile, kind))

            name = "index.html" if url.path in ("/", "/index.html") else url.path.lstrip("/")
            if name in {"index.html", "app.js", "style.css"}:
                data = (STATIC / name).read_bytes()
                ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
                return self._send(200, data, f"{ctype}; charset=utf-8" if ctype.startswith("text") or "javascript" in ctype else ctype, cache=True)
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/verify":
                return self._json(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise ValueError
                body = json.loads(self.rfile.read(length))
                token, answer = str(body["token"]), str(body["answer"])[:64]
            except (ValueError, KeyError, TypeError):
                return self._json(400, {"error": "bad request"})

            profile = self._profile(body.get("profile"))
            if not profile:
                return self._json(400, {"error": "unknown profile"})

            result = service.verify(token, answer)
            payload = {"ok": result.ok, "reason": result.reason, "attempts_left": result.attempts_left}
            # Anything but success gets a fresh challenge so the UI can keep going.
            if not result.ok:
                payload["challenge"] = self._challenge_payload(profile, body.get("kind"))
            self._json(200, payload)

        def log_message(self, fmt, *args) -> None:  # keep logs free of client details
            return

    return Handler


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    service: Optional[ChallengeService] = None,
    profiles: Optional[Dict[str, Profile]] = None,
) -> ThreadingHTTPServer:
    service = service or ChallengeService()
    return ThreadingHTTPServer((host, port), make_handler(service, profiles or PROFILES))


def serve_in_thread(server: ThreadingHTTPServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread
