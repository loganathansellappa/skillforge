"""Unit tests for the optional pr-responder slop-guard example hook."""
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = (Path(__file__).resolve().parent.parent
        / "skills" / "pr-responder" / "hooks" / "slop-guard-hook.example.py")


def run_hook(cmd):
    payload = {"toolName": "powershell", "toolArgs": {"command": cmd}}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload), capture_output=True, text=True, env=dict(os.environ),
    )
    assert proc.returncode == 0, f"hook must exit 0, got {proc.returncode}: {proc.stderr}"
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def denied(decision):
    return decision.get("permissionDecision") == "deny"


class SlopGuardExampleHook(unittest.TestCase):
    def test_em_dash_body_denied(self):
        cmd = ('gh api repos/o/r/pulls/7/comments -f body="Great \u2014 done"')
        self.assertTrue(denied(run_hook(cmd)))

    def test_curly_quote_body_denied(self):
        cmd = ('curl -X POST -d \'{"body":"\u201cfixed\u201d"}\' '
               'https://api.github.com/repos/o/r/issues/7/comments')
        self.assertTrue(denied(run_hook(cmd)))

    def test_emoji_body_denied(self):
        cmd = ('glab api -X POST projects/1/merge_requests/2/notes -f body="done \U0001F680"')
        self.assertTrue(denied(run_hook(cmd)))

    def test_clean_body_allowed(self):
        cmd = ('gh api repos/o/r/pulls/7/comments -f body="Good catch, added a TTL."')
        self.assertEqual(run_hook(cmd), {})

    def test_listing_comments_allowed(self):
        self.assertEqual(run_hook("gh api repos/o/r/pulls/7/comments"), {})

    def test_unrelated_command_allowed(self):
        self.assertEqual(run_hook("git status"), {})

    def test_empty_payload_allows(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input="", capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout.strip()
        self.assertEqual(json.loads(out) if out else {}, {})


if __name__ == "__main__":
    unittest.main()
