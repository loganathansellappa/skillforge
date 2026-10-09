"""Unit tests for the pr-responder grounding gate (skills/pr-responder/ground.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "skills" / "pr-responder"))

import ground  # noqa: E402


class ExtractRefsTests(unittest.TestCase):
    def test_file_line_and_bare_path(self):
        files, filelines, shas = ground.extract_refs("see src/auth.py:42 and config.yaml")
        self.assertIn("src/auth.py", files)
        self.assertIn("config.yaml", files)
        self.assertIn(("src/auth.py", 42), filelines)

    def test_prose_abbreviations_are_not_paths(self):
        files, _, _ = ground.extract_refs("do it, e.g. carefully, i.e. now")
        self.assertEqual(files, set())

    def test_shas_lowercased(self):
        _, _, shas = ground.extract_refs("fixed in A1B2C3D")
        self.assertIn("a1b2c3d", shas)

    def test_hex_english_word_is_captured_as_sha(self):
        # 'feedbac' is 7 hex chars; it is only acted on in strict mode, by design.
        _, _, shas = ground.extract_refs("thanks for the feedbac")
        self.assertIn("feedbac", shas)


class BodyOkTests(unittest.TestCase):
    def test_empty_rejected(self):
        ok, _ = ground.body_ok("   ")
        self.assertFalse(ok)

    def test_placeholder_rejected(self):
        for p in ("...", "TODO", "FIXME", "<fill>", "n/a"):
            ok, _ = ground.body_ok(p)
            self.assertFalse(ok, p)

    def test_real_body_ok(self):
        ok, _ = ground.body_ok("Good catch, fixed the TTL.")
        self.assertTrue(ok)


class FileGroundedTests(unittest.TestCase):
    def setUp(self):
        self.changed = {"src/auth/login.py", "docs/readme.md"}

    def test_exact_path(self):
        self.assertTrue(ground._file_grounded("src/auth/login.py", self.changed))

    def test_suffix_path(self):
        self.assertTrue(ground._file_grounded("auth/login.py", self.changed))

    def test_bare_basename(self):
        self.assertTrue(ground._file_grounded("login.py", self.changed))

    def test_unknown_file(self):
        self.assertFalse(ground._file_grounded("src/other.py", self.changed))


class GroundCheckTests(unittest.TestCase):
    def setUp(self):
        self.changed = {"src/auth.py", "src/cache.py"}
        self.shas = {"a1b2c3d4e5f6", "0011223344556677"}

    def test_cites_nothing_passes(self):
        ok, reasons = ground.ground_check("Good catch, done.", self.changed)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_grounded_file_passes(self):
        ok, _ = ground.ground_check("fixed in src/auth.py:10", self.changed)
        self.assertTrue(ok)

    def test_ungrounded_file_fails(self):
        ok, reasons = ground.ground_check("see src/ghost.py", self.changed)
        self.assertFalse(ok)
        self.assertTrue(any("ghost.py" in r for r in reasons))

    def test_sha_ignored_without_strict(self):
        ok, _ = ground.ground_check("fixed in deadbee", self.changed, shas=self.shas)
        self.assertTrue(ok)

    def test_strict_sha_match_passes(self):
        ok, _ = ground.ground_check("fixed in a1b2c3d", self.changed,
                                     shas=self.shas, strict=True)
        self.assertTrue(ok)

    def test_strict_unknown_sha_fails(self):
        ok, reasons = ground.ground_check("fixed in src/auth.py in cafed00",
                                          self.changed, shas=self.shas, strict=True)
        self.assertFalse(ok)
        self.assertTrue(any("commit" in r for r in reasons))

    def test_repo_root_accepts_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "helper.py").write_text("x = 1\n", encoding="utf-8")
            ok, _ = ground.ground_check("see helper.py", self.changed, repo_root=d)
            self.assertTrue(ok)

    def test_strict_ignores_repo_root(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "helper.py").write_text("x = 1\n", encoding="utf-8")
            ok, _ = ground.ground_check("see helper.py", self.changed,
                                        repo_root=d, strict=True)
            self.assertFalse(ok)


class CliTests(unittest.TestCase):
    def _write(self, lines):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        f.write("\n".join(lines))
        f.close()
        return f.name

    def test_no_files_from_skips_but_passes_body(self):
        rc = ground.main(["--text", "Good catch, done."])
        self.assertEqual(rc, 0)

    def test_empty_body_fails_before_ground_truth(self):
        rc = ground.main(["--text", "   "])
        self.assertEqual(rc, 4)

    def test_grounded_cli_passes(self):
        files = self._write(["src/auth.py", "src/cache.py"])
        rc = ground.main(["--text", "fixed src/auth.py:10", "--files-from", files])
        self.assertEqual(rc, 0)

    def test_ungrounded_cli_fails(self):
        files = self._write(["src/auth.py"])
        rc = ground.main(["--text", "see src/ghost.py", "--files-from", files])
        self.assertEqual(rc, 4)


if __name__ == "__main__":
    unittest.main()
