import json
import random
import time
import unittest
import urllib.error
import urllib.request

from humancheck import ChallengeService, Verifier, render
from humancheck.challenges import ALPHABET, ChallengeSpec, make_spec, math_spec, normalize
from humancheck.profiles import PROFILES, get_profile
from humancheck.server import create_server, serve_in_thread


class ChallengeTests(unittest.TestCase):
    def test_text_alphabet_has_no_lookalikes(self):
        for ch in "0O1IL":
            self.assertNotIn(ch, ALPHABET)
        spec = make_spec("text", 8)
        self.assertEqual(len(spec.answer), 8)
        self.assertTrue(set(spec.answer) <= set(ALPHABET))

    def test_math_answers_are_correct_and_positive(self):
        for _ in range(300):
            spec = math_spec()
            a, op, b = spec.display.replace(" = ?", "").split(" ")
            a, b = int(a), int(b)
            expected = {"+": a + b, "\u2212": a - b, "\u00d7": a * b}[op]
            self.assertEqual(int(spec.answer), expected)
            self.assertGreater(expected, 0)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            make_spec("audio")

    def test_normalize(self):
        self.assertEqual(normalize("  aB 3 "), "ab3")


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.v = Verifier(secret=b"k" * 32, ttl=60, max_attempts=3)

    def test_correct_answer_is_case_insensitive(self):
        token = self.v.issue("K7M4QX")
        self.assertTrue(self.v.check(token, "k7m4qx").ok)

    def test_token_does_not_contain_answer(self):
        self.assertNotIn("K7M4QX".lower(), self.v.issue("K7M4QX").lower())

    def test_single_use(self):
        token = self.v.issue("ABC")
        self.assertTrue(self.v.check(token, "abc").ok)
        self.assertEqual(self.v.check(token, "abc").reason, "used")

    def test_attempt_limit(self):
        token = self.v.issue("ABC")
        reasons = [self.v.check(token, "nope").reason for _ in range(3)]
        self.assertEqual(reasons, ["wrong", "wrong", "exhausted"])
        self.assertEqual(self.v.check(token, "abc").reason, "exhausted")

    def test_expiry(self):
        token = self.v.issue("ABC", ttl=-1)
        self.assertEqual(self.v.check(token, "abc").reason, "expired")

    def test_tampering_and_garbage(self):
        token = self.v.issue("ABC")
        head, sig = token.rsplit(".", 1)
        self.assertEqual(self.v.check(head + "." + sig[::-1], "abc").reason, "invalid")
        for junk in ("", "a.b.c", "x" * 300, "1.2.3.4"):
            self.assertEqual(self.v.check(junk, "abc").reason, "invalid")

    def test_other_secret_rejected(self):
        other = Verifier(secret=b"z" * 32)
        self.assertEqual(other.check(self.v.issue("ABC"), "abc").reason, "invalid")


class RendererTests(unittest.TestCase):
    def test_size_and_seed_determinism(self):
        p = get_profile("ev-motors")
        a = render("ABCDE", p.size, p.palette, random.Random(1))
        b = render("ABCDE", p.size, p.palette, random.Random(1))
        self.assertEqual(a.size, p.size)
        self.assertEqual(a.tobytes(), b.tobytes())

    def test_every_profile_renders(self):
        for p in PROFILES.values():
            spec = make_spec(p.kind, p.length)
            self.assertEqual(render(spec.display, p.size, p.palette).size, p.size)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answers = {}
        svc = ChallengeService(
            Verifier(secret=b"t" * 32),
            spec_factory=lambda kind, n: ChallengeSpec(kind, "AB12", "AB12", "Type the characters you see"),
        )
        cls.server = create_server("127.0.0.1", 0, svc)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        serve_in_thread(cls.server)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return json.load(r)

    def post(self, path, payload, raw=None):
        req = urllib.request.Request(
            self.base + path, data=raw if raw is not None else json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_profiles_and_page(self):
        self.assertEqual({p["key"] for p in self.get("/api/profiles")}, set(PROFILES))
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"<title>", r.read())

    def test_public_profile_has_no_secrets(self):
        data = self.get("/api/profile/fintech")
        self.assertEqual(data["kind"], "math")
        self.assertNotIn("palette", data)

    def test_full_flow(self):
        ch = self.get("/api/challenge?profile=generic")
        self.assertTrue(ch["image"].startswith("data:image/png;base64,"))
        self.assertNotIn("answer", ch)
        status, bad = self.post("/api/verify", {"token": ch["token"], "answer": "zzzz", "profile": "generic"})
        self.assertEqual((status, bad["ok"], bad["reason"]), (200, False, "wrong"))
        self.assertIn("challenge", bad)                     # fresh challenge supplied
        status, good = self.post("/api/verify", {"token": bad["challenge"]["token"], "answer": "ab12", "profile": "generic"})
        self.assertTrue(good["ok"])

    def test_bad_requests(self):
        self.assertEqual(self.post("/api/verify", None, raw=b"not json")[0], 400)
        self.assertEqual(self.post("/api/verify", {"token": "x"})[0], 400)
        self.assertEqual(self.post("/api/verify", None, raw=b"{" + b" " * 5000 + b"}")[0], 400)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/api/challenge?profile=nope")
        self.assertEqual(cm.exception.code, 400)

    def test_no_path_traversal(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + "/../config.py")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
