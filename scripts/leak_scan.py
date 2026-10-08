#!/usr/bin/env python3
"""Repo-wide leak scanner for skillforge — keep every skill generic and private-data-free.

skillforge is a PUBLIC collection of portable agent skills. Nothing in it may
contain company/product names, private hosts, personal paths, secrets, or
internal ticket ids. This script enforces that policy in code so a slip is caught
locally and in CI instead of after it ships.

It is deliberately company-AGNOSTIC — it names no company itself. Two layers:
  1. Generic leak-CLASS patterns baked in below (high signal, low noise):
     personal home paths, absolute drive paths, private VCS hosts/URLs, emails,
     IP addresses, obvious secret tokens, and internal ticket ids.
  2. An OPTIONAL, gitignored local denylist (scripts/company-terms.txt) where a
     maintainer lists the actual product/host/user names to catch. The committed
     repo never contains that file, so the names themselves never leak either.

Exit 0 = clean, 1 = findings, 2 = usage error. Stdlib only; no network.
"""
import argparse
import re
import sys
from pathlib import Path

SCAN_EXT = {".md", ".py", ".yml", ".yaml", ".txt", ".json", ".sh", ".ps1",
            ".cfg", ".ini", ".toml", ".js", ".ts"}
SCAN_SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".secrets",
                  # tests hold deliberate fake-leak fixtures for this scanner.
                  "tests"}
# Files that legitimately contain leak-like literals (this scanner's own
# patterns, and the local denylist) — never scan them for leaks.
SCAN_SKIP_RELPATHS = {"scripts/leak_scan.py", "scripts/company-terms.txt"}
DEFAULT_TERMS_REL = "scripts/company-terms.txt"

# JIRA-style internal ticket ids (e.g. ABC-1234). Case-sensitive prefix so
# lowercase tokens like "utf-8" or "opus-4" are ignored.
TICKET_RE = re.compile(r"\b[A-Z]{2,10}-\d{1,6}\b")
TICKET_PREFIX_ALLOW = {"ISO", "UTF", "SHA", "RFC", "AES", "RSA", "MD", "EC",
                       "CVE", "HTTP", "IPV", "PBKDF", "TLS", "SSL", "UTC", "GPT"}
TICKET_PLACEHOLDER_NUM = re.compile(r"^(?:0+|1|12|123|1234|12345|123456)$")
# Personal home directories (Windows profile + unix home).
HOMEPATH_RE = re.compile(r"C:\\Users\\[A-Za-z0-9._-]+|/(?:home|Users)/[A-Za-z0-9._-]+/")
# Absolute drive paths other than the placeholder-friendly cases.
DRIVEPATH_RE = re.compile(r"(?<![A-Za-z0-9])[D-Z]:\\[A-Za-z0-9_.\\-]+")
# Private VCS hosting / internal-network hints.
PRIVATE_HOST_RE = re.compile(
    r"\bssh://[\w.-]+|\bgit@[\w.-]+|\b[\w.-]+\.(?:internal|corp|intranet|local|lan)\b", re.I)
# Real-looking email addresses (allow noreply/example/placeholder domains).
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
EMAIL_ALLOW_DOMAINS = ("example.com", "example.org", "example.net",
                       "users.noreply.github.com", "localhost")
# Public documentation IPs / placeholders are fine; flag anything else.
IP_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
IP_ALLOW = {"127.0.0.1", "0.0.0.0", "255.255.255.255", "1.2.3.4",
            "10.0.0.1", "192.168.1.1", "192.168.0.1", "8.8.8.8"}
# Obvious secret tokens (not exhaustive — a tripwire, not a vault).
SECRET_RES = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                      # AWS access key id
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),            # GitHub tokens
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),          # Slack tokens
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def _is_ticketish(tok):
    prefix, _, num = tok.partition("-")
    if prefix in TICKET_PREFIX_ALLOW:
        return False
    if TICKET_PLACEHOLDER_NUM.match(num):
        return False
    return True


def load_terms(terms_path):
    """Load the optional local denylist (one term per line; '#' comments)."""
    p = Path(terms_path)
    terms = []
    if p.is_file():
        for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                terms.append(ln)
    return terms


def scan_file(rel, text, term_res):
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in HOMEPATH_RE.finditer(line):
            findings.append(f"{rel}:{i} : personal path '{m.group(0)}'")
        for m in DRIVEPATH_RE.finditer(line):
            findings.append(f"{rel}:{i} : absolute drive path '{m.group(0)}' (use a placeholder)")
        for m in PRIVATE_HOST_RE.finditer(line):
            findings.append(f"{rel}:{i} : private host/URL '{m.group(0)}'")
        for m in EMAIL_RE.finditer(line):
            email = m.group(0)
            if not email.lower().endswith(EMAIL_ALLOW_DOMAINS):
                findings.append(f"{rel}:{i} : email address '{email}' (use an example.com placeholder)")
        for m in IP_RE.finditer(line):
            ip = m.group(0)
            octs = ip.split(".")
            if all(0 <= int(o) <= 255 for o in octs) and ip not in IP_ALLOW:
                findings.append(f"{rel}:{i} : IP address '{ip}' (use a doc placeholder)")
        for rx in SECRET_RES:
            m = rx.search(line)
            if m:
                findings.append(f"{rel}:{i} : possible secret token '{m.group(0)[:12]}…'")
        for tok in TICKET_RE.findall(line):
            if _is_ticketish(tok):
                findings.append(f"{rel}:{i} : internal ticket id '{tok}' (strip or use a placeholder)")
        for term, rx in term_res:
            if rx.search(line):
                findings.append(f"{rel}:{i} : denylisted term '{term}' (keep skillforge generic)")
    return findings


def scan_repo(root, terms, terms_path=None):
    findings = []
    term_res = [(t, re.compile(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", re.I))
                for t in terms]
    terms_resolved = Path(terms_path).resolve() if terms_path else None
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in SCAN_EXT:
            continue
        if any(part in SCAN_SKIP_DIRS for part in f.relative_to(root).parts):
            continue
        rel = f.relative_to(root).as_posix()
        if rel in SCAN_SKIP_RELPATHS:
            continue
        if terms_resolved and f.resolve() == terms_resolved:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        findings.extend(scan_file(rel, text, term_res))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="skillforge leak scanner (keep it generic).")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="Repo root (defaults to parent of scripts/)")
    ap.add_argument("--terms", default="",
                    help="Optional local denylist file (default: <root>/scripts/company-terms.txt)")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2
    terms_path = args.terms or str(root / DEFAULT_TERMS_REL)
    findings = scan_repo(root, load_terms(terms_path), terms_path)
    if findings:
        print(f"leak-scan: {len(findings)} finding(s):")
        for x in findings:
            print(f"  ! {x}")
        print("leak-scan: FAIL")
        return 1
    print("leak-scan: PASS (no leaks detected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
