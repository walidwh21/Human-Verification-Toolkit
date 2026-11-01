"""Creating the question and its expected answer."""
from __future__ import annotations

import random
import secrets
from dataclasses import dataclass

# Characters that are easy to confuse (0/O, 1/I/L) are left out.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

_rng = secrets.SystemRandom()


@dataclass(frozen=True)
class ChallengeSpec:
    kind: str       # "text" | "math"
    display: str    # what is drawn into the image
    answer: str     # what the person must type
    prompt: str     # short instruction for the UI


def normalize(value: str) -> str:
    """Make comparison forgiving about case and stray spaces."""
    return "".join(str(value).split()).casefold()


def text_spec(length: int = 6, rng: random.Random = _rng) -> ChallengeSpec:
    chars = "".join(rng.choice(ALPHABET) for _ in range(length))
    return ChallengeSpec("text", chars, chars, "Type the characters you see")


def math_spec(rng: random.Random = _rng) -> ChallengeSpec:
    op = rng.choice("+-x")
    if op == "+":
        a, b = rng.randint(3, 19), rng.randint(2, 9)
        result = a + b
    elif op == "-":
        a = rng.randint(8, 25)
        b = rng.randint(2, a - 1)
        result = a - b
    else:
        a, b = rng.randint(2, 9), rng.randint(2, 9)
        result = a * b
    shown_op = {"+": "+", "-": "\u2212", "x": "\u00d7"}[op]
    return ChallengeSpec("math", f"{a} {shown_op} {b} = ?", str(result), "Solve the sum")


def make_spec(kind: str, length: int = 6, rng: random.Random = _rng) -> ChallengeSpec:
    if kind == "text":
        return text_spec(length, rng)
    if kind == "math":
        return math_spec(rng)
    raise ValueError(f"Unknown challenge kind: {kind!r}")
