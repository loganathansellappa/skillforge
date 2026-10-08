#!/usr/bin/env python3
"""One-command gate for skillforge. Runs, in order:

  1. leak_scan.py        — repo must contain no private/company data
  2. skill frontmatter   — every skills/<name>/SKILL.md has valid name+description
  3. unit tests          — tests/ (the leak-scanner's own tests, etc.)

Exit 0 only if all pass. Stdlib only; no network. Run before every commit/push
and in CI.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SKILLS = ROOT / "skills"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _run(title, fn):
    print("=" * 70)
    print(f"== {title}")
    print("=" * 70)
    ok = fn()
    print(f"-- {title}: {'PASS' if ok else 'FAIL'}")
    return ok


def check_leaks():
    rc = subprocess.run([sys.executable, str(SCRIPTS / "leak_scan.py")]).returncode
    return rc == 0


def check_skill_frontmatter():
    ok = True
    skills = sorted(p for p in SKILLS.glob("*/SKILL.md")) if SKILLS.is_dir() else []
    if not skills:
        print("  ! no skills/<name>/SKILL.md found")
        return False
    for sk in skills:
        name = sk.parent.name
        text = sk.read_text(encoding="utf-8", errors="ignore")
        m = FRONTMATTER_RE.match(text)
        if not m:
            print(f"  ! {name}: missing YAML frontmatter block")
            ok = False
            continue
        fm = m.group(1)
        has_name = re.search(r"^name:\s*\S+", fm, re.M)
        has_desc = re.search(r"^description:\s*\S+", fm, re.M)
        fm_name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not has_name:
            print(f"  ! {name}: frontmatter missing 'name:'")
            ok = False
        elif fm_name and fm_name.group(1).strip() != name:
            print(f"  ! {name}: frontmatter name '{fm_name.group(1).strip()}' != folder '{name}'")
            ok = False
        if not has_desc:
            print(f"  ! {name}: frontmatter missing 'description:'")
            ok = False
        if has_name and has_desc and (not fm_name or fm_name.group(1).strip() == name):
            print(f"  [ok] {name}")
    return ok


def check_tests():
    tests_dir = ROOT / "tests"
    if not tests_dir.is_dir() or not any(tests_dir.glob("test_*.py")):
        print("  (no tests found — skipping)")
        return True
    loader = unittest.TestLoader()
    suite = loader.discover(str(tests_dir), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return result.wasSuccessful()


def main():
    results = {
        "Leak scan (leak_scan.py)": _run("Leak scan (leak_scan.py)", check_leaks),
        "Skill frontmatter lint": _run("Skill frontmatter lint", check_skill_frontmatter),
        "Unit tests": _run("Unit tests", check_tests),
    }
    print("=" * 70)
    print("== VERIFY SUMMARY")
    print("=" * 70)
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    gate = all(results.values())
    print(f"\nGate: {'PASS' if gate else 'FAIL'}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
