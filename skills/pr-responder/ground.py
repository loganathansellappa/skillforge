#!/usr/bin/env python3
"""The grounding gate: prove a PR reply points at code that is really in the PR.

One job. Before you post a reply or a review comment, check that it is not a
structural false positive. It rejects a draft whose body is empty or a placeholder,
and a draft that cites a file (or file:line, or commit sha) that does not belong to
THIS pull request. That catches the replies that cite a made-up path, the wrong
file, or a commit from another branch, the kind of mistake a reader spots at once
and stops trusting the rest.

What it does NOT do: it cannot tell whether the reply is correct or actually answers
the comment. That stays your job. A reply can be perfectly grounded and still wrong.
Read the cited code and make the reply address the point.

This gate is host-neutral and does no network call of its own. You give it the PR's
real changed files (and, if you want the sha check, the PR's commits), which you
already fetch with your host's list command (see references/hosts.md). It compares
what the draft cites against what you give it.

Usage:
  # 1) capture the PR's changed files with your host command, one path per line:
  gh pr diff <pr> --name-only > /tmp/pr-files.txt           # GitHub
  glab mr diff <iid> --raw | ...                            # GitLab (see hosts.md)

  # 2) check a draft against them:
  python ground.py --text "see auth.py:42, fixed in a1b2c3d" --files-from /tmp/pr-files.txt
  echo "your draft" | python ground.py --files-from /tmp/pr-files.txt

  # stricter: also require every cited commit sha to be a PR commit
  python ground.py --text "..." --files-from pr-files.txt --shas-from pr-shas.txt --strict

  # local checkout fallback: accept a cited file that exists on disk even if it is
  # not in the diff (a file you reference for context but did not change)
  python ground.py --text "..." --files-from pr-files.txt --repo-root .

Exit codes:
  0  grounded (or nothing to check): safe to continue to the humanize gate and post
  4  ungrounded: fix the references, do not post

Stdlib only. No host CLI, no token, no network. Pairs with humanize.py: run this
first (is the reply pointing at real code?), then humanize.py (does it read human?).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# File extensions that mark a bare token as a code path, so prose like "e.g." or
# "i.e." is never mistaken for a file.
_CODE_EXT = (
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".cpp", ".cc", ".cxx",
    ".h", ".hpp", ".hh", ".cs", ".rb", ".rs", ".kt", ".kts", ".swift", ".m", ".mm",
    ".php", ".scala", ".sql", ".sh", ".ps1", ".psm1", ".yaml", ".yml", ".json",
    ".xml", ".gradle", ".toml", ".ini", ".cfg", ".md", ".proto", ".vue", ".css",
    ".scss", ".html", ".tf", ".bicep", ".dockerfile",
)
_FILELINE_RE = re.compile(r"\b([\w./\-]+\.[A-Za-z0-9]+):(\d+)(?:-\d+)?\b")
_PATH_RE = re.compile(r"\b([\w./\-]*[\w\-]+\.[A-Za-z0-9]+)\b")
_SHA_RE = re.compile(r"\b([0-9a-fA-F]{7,40})\b")
_PLACEHOLDER_RE = re.compile(r"^(?:\.{2,}|todo|tbd|wip|xxx|fixme|<[^>]*>|n/?a)$", re.I)


def _looks_like_path(tok: str) -> bool:
    ext = "." + tok.rsplit(".", 1)[-1].lower() if "." in tok else ""
    return ("/" in tok and "." in tok.rsplit("/", 1)[-1]) or ext in _CODE_EXT


def extract_refs(text: str):
    """Return (file_tokens, [(path, line)], sha_tokens) cited in the text."""
    files, filelines, shas = set(), [], set()
    for m in _FILELINE_RE.finditer(text):
        files.add(m.group(1))
        filelines.append((m.group(1), int(m.group(2))))
    for m in _PATH_RE.finditer(text):
        tok = m.group(1).strip(".,);:'\"")
        if _looks_like_path(tok):
            files.add(tok)
    for m in _SHA_RE.finditer(text):
        shas.add(m.group(1).lower())
    return files, filelines, shas


def body_ok(text: str):
    stripped = text.strip()
    if not stripped:
        return False, "empty body"
    if _PLACEHOLDER_RE.match(stripped):
        return False, f"placeholder body: {stripped!r}"
    return True, ""


def _file_grounded(tok, changed):
    """A cited path matches the PR's changed-file set by exact path, suffix, or
    (when the citation has no directory) bare basename."""
    tok = tok.lstrip("./")
    if not tok:
        return False
    base = tok.rsplit("/", 1)[-1]
    for cf in changed:
        if cf == tok or cf.endswith("/" + tok):
            return True
        if "/" not in tok and cf.rsplit("/", 1)[-1] == base:
            return True
    return False


def _exists_in_checkout(tok, repo_root):
    """Accept a cited file that exists on disk under repo_root, for a file the
    reply references for context but did not change."""
    tok = tok.lstrip("./")
    if not tok:
        return False
    root = Path(repo_root)
    if (root / tok).is_file():
        return True
    base = tok.rsplit("/", 1)[-1]
    try:
        return any(p.is_file() for p in root.rglob(base))
    except OSError:
        return False


def _read_lines(path):
    if not path:
        return None
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    return {ln.strip() for ln in raw.splitlines() if ln.strip()}


def ground_check(text, changed, shas=None, repo_root=None, strict=False):
    """Return (ok, reasons). changed is the PR's changed-file set. shas (optional)
    is the PR's commit-sha set, checked only with strict. A draft that cites nothing
    passes."""
    reasons = []
    files, filelines, cited_shas = extract_refs(text)

    for tok in sorted(files):
        if _file_grounded(tok, changed):
            continue
        if not strict and repo_root and _exists_in_checkout(tok, repo_root):
            continue
        reasons.append(f"cited file not in this PR: {tok}")

    if strict and shas is not None:
        norm = {s.lower() for s in shas}
        for s in sorted(cited_shas):
            if not any(h == s or h.startswith(s) or s.startswith(h) for h in norm):
                reasons.append(f"cited commit not in this PR: {s}")

    return (not reasons), reasons


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grounding gate for PR text.")
    ap.add_argument("--text", help="draft text (or pipe it on stdin)")
    ap.add_argument("--files-from", help="file listing the PR's changed paths, one per line")
    ap.add_argument("--shas-from", help="file listing the PR's commit shas, one per line (for --strict)")
    ap.add_argument("--repo-root", help="local checkout root; accept cited files that exist here (ignored with --strict)")
    ap.add_argument("--strict", action="store_true",
                    help="require cited files to be in the diff AND cited shas to be PR commits")
    args = ap.parse_args(argv)

    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    text = args.text if args.text is not None else sys.stdin.read()

    ok, why = body_ok(text)
    if not ok:
        sys.stderr.write(f"UNGROUNDED: {why}\n")
        return 4

    if not args.files_from:
        sys.stderr.write(
            "NO GROUND TRUTH: pass --files-from with the PR's changed files to run the "
            "grounding check (see references/hosts.md for the list command). Skipping.\n"
        )
        return 0

    changed = _read_lines(args.files_from) or set()
    shas = _read_lines(args.shas_from)

    ok, reasons = ground_check(text, changed, shas=shas, repo_root=args.repo_root, strict=args.strict)
    if ok:
        sys.stderr.write("GROUNDED\n")
        return 0
    sys.stderr.write("UNGROUNDED\n  " + "\n  ".join(reasons) + "\n")
    return 4


if __name__ == "__main__":
    sys.exit(main())
