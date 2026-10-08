"""Unit tests for scripts/leak_scan.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import leak_scan  # noqa: E402


class ScanFileTests(unittest.TestCase):
    def scan(self, text, terms=None):
        term_res = [(t, __import__("re").compile(
            r"(?<![A-Za-z0-9])" + __import__("re").escape(t) + r"(?![A-Za-z0-9])",
            __import__("re").I)) for t in (terms or [])]
        return leak_scan.scan_file("x.md", text, term_res)

    def test_clean_text_has_no_findings(self):
        self.assertEqual(self.scan("A plain sentence about code."), [])

    def test_personal_path(self):
        self.assertTrue(any("personal path" in f
                            for f in self.scan(r"see C:\Users\alice\notes.txt")))

    def test_absolute_drive_path(self):
        self.assertTrue(any("absolute drive path" in f
                            for f in self.scan(r"path is D:\work\repo")))

    def test_private_host(self):
        self.assertTrue(any("private host" in f
                            for f in self.scan("deploy to build.corp.intranet")))

    def test_real_email_flagged(self):
        self.assertTrue(any("email" in f
                            for f in self.scan("ping bob@contoso.com please")))

    def test_example_email_allowed(self):
        self.assertEqual(self.scan("write to someone@example.com"), [])

    def test_github_noreply_allowed(self):
        self.assertEqual(self.scan("1+1@users.noreply.github.com"), [])

    def test_real_ip_flagged(self):
        self.assertTrue(any("IP address" in f
                            for f in self.scan("host at 203.0.113.9 today")))

    def test_doc_ip_allowed(self):
        self.assertEqual(self.scan("localhost is 127.0.0.1 here"), [])

    def test_secret_token(self):
        self.assertTrue(any("secret" in f
                            for f in self.scan("key=AKIAIOSFODNN7EXAMPLE")))

    def test_ticket_id_flagged(self):
        self.assertTrue(any("ticket" in f
                            for f in self.scan("fixed in PROJ-4821 yesterday")))

    def test_standard_prefix_not_ticket(self):
        self.assertEqual(self.scan("per RFC-2119 and UTF-8"), [])

    def test_placeholder_ticket_allowed(self):
        self.assertEqual(self.scan("example id ABC-123"), [])

    def test_denylist_term(self):
        findings = self.scan("we use Contoso here", terms=["Contoso"])
        self.assertTrue(any("denylisted term" in f for f in findings))

    def test_denylist_is_case_insensitive(self):
        findings = self.scan("we use contoso here", terms=["Contoso"])
        self.assertTrue(any("denylisted term" in f for f in findings))


class LoadTermsTests(unittest.TestCase):
    def test_load_terms_skips_comments_and_blanks(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "terms.txt"
            p.write_text("# comment\nContoso\n\n  Fabrikam  \n", encoding="utf-8")
            self.assertEqual(leak_scan.load_terms(p), ["Contoso", "Fabrikam"])

    def test_load_terms_missing_file(self):
        self.assertEqual(leak_scan.load_terms("does-not-exist.txt"), [])


if __name__ == "__main__":
    unittest.main()
