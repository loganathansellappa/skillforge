"""Unit tests for the pr-responder humanize gate (skills/pr-responder/humanize.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "skills" / "pr-responder"))

import humanize  # noqa: E402


class SanitizeTests(unittest.TestCase):
    def test_em_and_en_dash_become_hyphen(self):
        self.assertEqual(humanize.sanitize("a \u2014 b \u2013 c"), "a - b - c")

    def test_curly_quotes_become_straight(self):
        self.assertEqual(humanize.sanitize("\u201chi\u201d \u2018yo\u2019"), '"hi" \'yo\'')

    def test_ellipsis_and_nbsp(self):
        self.assertEqual(humanize.sanitize("wait\u2026\u00a0ok"), "wait... ok")

    def test_emoji_removed(self):
        self.assertEqual(humanize.sanitize("nice \U0001F680 work"), "nice work")

    def test_collapses_double_spaces(self):
        self.assertEqual(humanize.sanitize("a    b"), "a b")

    def test_plain_text_unchanged(self):
        plain = "Added a one minute TTL and a test."
        self.assertEqual(humanize.sanitize(plain), plain)


class LintTests(unittest.TestCase):
    def test_missing_tool_is_treated_as_human(self):
        # When slophound is absent, lint must degrade to a skip, not a block.
        import shutil
        if shutil.which("slophound"):
            self.skipTest("slophound is installed; the skip path is not exercised")
        ok, report = humanize.lint("any text")
        self.assertTrue(ok)
        self.assertIn("skipped", report)


class CliTests(unittest.TestCase):
    def test_sanitize_only_exits_zero(self):
        rc = humanize.main(["--text", "a \u2014 b", "--sanitize-only"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
