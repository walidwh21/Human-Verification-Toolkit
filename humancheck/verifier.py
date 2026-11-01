"""Signed, expiring, single-use challenge tokens.

The token carries only a keyed digest of the answer, never the answer itself,
so it can be handed to the browser safely. Attempt counting and replay
protection live in memory; use one ``Verifier`` per process (or back it with a
shared store if you run several workers).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

from .challenges import normalize


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    reason: str            # ok | wrong | expired | invalid | used | exhausted
    attempts_left: int = 0


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class Verifier:
    def __init__(self, secret: Optional[bytes] = None, ttl: int = 180, max_attempts: int = 3):
        env = os.environ.get("HUMANCHECK_SECRET")
        self._secret = secret or (env.encode() if env else secrets.token_bytes(32))
        self.ttl = ttl
        self.max_attempts = max_attempts
        self._attempts: Dict[str, int] = {}
        self._done: Dict[str, float] = {}
        self._lock = threading.Lock()

    # -- internals ---------------------------------------------------------
    def _mac(self, *parts: str) -> bytes:
        return hmac.new(self._secret, "|".join(parts).encode(), hashlib.sha256).digest()

    def _purge(self, now: float) -> None:
        for nonce in [n for n, exp in self._done.items() if exp < now]:
            self._done.pop(nonce, None)
            self._attempts.pop(nonce, None)

    # -- public API --------------------------------------------------------
    def issue(self, answer: str, ttl: Optional[int] = None) -> str:
        nonce = secrets.token_hex(8)
        expires = int(time.time()) + (ttl or self.ttl)
        digest = self._mac("ans", nonce, normalize(answer))[:16]
        body = f"{nonce}.{expires}.{_b64(digest)}"
        return f"{body}.{_b64(self._mac('tok', body))}"

    def check(self, token: str, answer: str) -> VerifyResult:
        try:
            nonce, expires_s, digest_s, sig_s = token.split(".")
            body = f"{nonce}.{expires_s}.{digest_s}"
            if not hmac.compare_digest(_unb64(sig_s), self._mac("tok", body)):
                return VerifyResult(False, "invalid")
            expires = int(expires_s)
        except (ValueError, TypeError):
            return VerifyResult(False, "invalid")

        now = time.time()
        with self._lock:
            self._purge(now)
            if expires < now:
                return VerifyResult(False, "expired")
            if nonce in self._done and self._attempts.get(nonce, 0) < 0:
                return VerifyResult(False, "used")
            used = self._attempts.get(nonce, 0)
            if used >= self.max_attempts:
                return VerifyResult(False, "exhausted")

            expected = _unb64(digest_s)
            given = self._mac("ans", nonce, normalize(answer))[:16]
            if hmac.compare_digest(expected, given):
                self._attempts[nonce] = -1          # burn: single use
                self._done[nonce] = expires
                return VerifyResult(True, "ok", self.max_attempts - used - 1)

            used += 1
            self._attempts[nonce] = used
            self._done[nonce] = expires
            left = self.max_attempts - used
            return VerifyResult(False, "wrong" if left else "exhausted", left)
