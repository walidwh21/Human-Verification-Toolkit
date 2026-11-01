"""High-level API: create a challenge, verify an answer."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Optional

from .challenges import ChallengeSpec, make_spec
from .config import Profile
from .renderer import render, to_png_bytes
from .verifier import Verifier, VerifyResult


@dataclass(frozen=True)
class Challenge:
    token: str
    kind: str
    prompt: str
    png: bytes
    expires_in: int


class ChallengeService:
    """``spec_factory`` lets tests and screenshot tools supply fixed answers."""

    def __init__(
        self,
        verifier: Optional[Verifier] = None,
        spec_factory: Optional[Callable[[str, int], ChallengeSpec]] = None,
    ):
        self.verifier = verifier or Verifier()
        self._spec_factory = spec_factory or (lambda kind, length: make_spec(kind, length))

    def create(self, profile: Profile, kind: Optional[str] = None) -> Challenge:
        kind = kind or profile.kind
        spec = self._spec_factory(kind, profile.length)
        image = render(spec.display, profile.size, profile.palette, random.Random())
        token = self.verifier.issue(spec.answer, profile.ttl_seconds)
        return Challenge(token, spec.kind, spec.prompt, to_png_bytes(image), profile.ttl_seconds)

    def verify(self, token: str, answer: str) -> VerifyResult:
        return self.verifier.check(token, answer)
