#!/usr/bin/env python3
"""The humanize gate: make PR text read like a person wrote it, then prove it.

One job. Take a draft reply or review comment, strip the punctuation tells that
mark generated text, then lint what is left with slophound. If it still reads as
generated, reject it so you rewrite before posting.

Usage:
  python humanize.py --text "your draft"          # sanitize + lint, print clean text
  echo "your draft" | python humanize.py          # same, from stdin
  python humanize.py --text "..." --sanitize-only  # clean only, skip the lint

Exit codes:
  0  clean (or slophound not installed, so the lint is skipped)
  3  still reads as generated: rewrite it plainer, then rerun

Stdlib only. slophound is optional but recommended (the lint half of the gate).
Install it with:  pipx install slophound   (or)   uv tool install slophound
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys

# Punctuation and symbols that generated text reaches for. Replace with the plain
# forms a person types on a normal keyboard.
_SMART = {
    "\u2014": "-", "\u2013": "-",            # em / en dash -> hyphen
    "\u2018": "'", "\u2019": "'",            # curly single quotes
    "\u201c": '"', "\u201d": '"',            # curly double quotes
    "\u2026": "...", "\u00a0": " ",          # ellipsis, non-breaking space
}
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U00002190-\U000021FF\U0000FE0F]"
)


def sanitize(text: str) -> str:
    """Strip the punctuation tells and collapse stray whitespace."""
    for k, v in _SMART.items():
        text = text.replace(k, v)
    text = _EMOJI.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +\n", "\n", text)
    return text.strip()


def lint(text: str):
    """Run slophound on the text. Returns (is_human, report).

    A missing or crashing tool is treated as a skip (is_human True) so the gate
    degrades to sanitize-only rather than blocking you.
    """
    exe = shutil.which("slophound")
    if not exe:
        return True, "(slophound not installed; lint skipped)"
    p = subprocess.run([exe, "--formal", "--no-footer", "-"],
                       input=text, capture_output=True, text=True)
    if p.returncode == 2:
        return True, "(slophound failed; lint skipped)"
    return p.returncode == 0, (p.stdout or p.stderr).strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Humanize gate for PR text.")
    ap.add_argument("--text", help="draft text (or pipe it on stdin)")
    ap.add_argument("--sanitize-only", action="store_true",
                    help="clean the punctuation but skip the slophound lint")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    raw = args.text if args.text is not None else sys.stdin.read()
    cleaned = sanitize(raw)

    if args.sanitize_only:
        print(cleaned)
        return 0

    ok, report = lint(cleaned)
    sys.stderr.write(("HUMAN OK\n" if ok else "READS AS GENERATED\n") + report + "\n")
    print(cleaned)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
