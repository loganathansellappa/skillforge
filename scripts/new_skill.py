#!/usr/bin/env python3
"""Scaffold a new skill folder with a valid SKILL.md, references/, and examples/.

Usage:
    python scripts/new_skill.py my-skill-name "One line: what it solves."

Creates skills/<name>/ with frontmatter whose `name:` matches the folder, so
verify.py passes from the start. Refuses to overwrite an existing skill.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

SKILL_TEMPLATE = """---
name: {name}
description: >-
  {desc} Use when {trigger}.
---

# {title}

> **Solves:** {desc}

## When to use

Describe the trigger conditions here, so an agent knows when to load this skill.

## When not to use

List the cases this skill should decline, to avoid misfires.

## Method

Write the generic, step-by-step method. Fictional examples only — no company,
product, host, path, secret, or ticket data (CI runs `scripts/leak_scan.py`).

## Output contract

State exactly what the skill returns, and how it labels certainty.

## References

- `references/` — templates and deep-dives loaded on demand.
- `examples/` — fully fictional worked examples.
"""

README_TEMPLATE = """# {title}

{desc}

## Setup

No install step. Point your agent at `SKILL.md`; see the repo root `README.md`
for per-platform wiring (Copilot, Claude, OpenCode).

## Usage

Describe how a user invokes the skill and what they get back.
"""


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python scripts/new_skill.py <name> [\"one-line description\"]",
              file=sys.stderr)
        return 2
    name = argv[0].strip().lower().replace(" ", "-")
    desc = (argv[1].strip() if len(argv) > 1 else "TODO: one line on what this solves.")
    title = name.replace("-", " ").title()
    dest = SKILLS / name
    if dest.exists():
        print(f"ERROR: skill already exists: {dest}", file=sys.stderr)
        return 1
    (dest / "references").mkdir(parents=True)
    (dest / "examples").mkdir(parents=True)
    (dest / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, desc=desc, title=title,
                              trigger="TODO describe the trigger"),
        encoding="utf-8")
    (dest / "README.md").write_text(
        README_TEMPLATE.format(title=title, desc=desc), encoding="utf-8")
    (dest / "references" / ".gitkeep").write_text("", encoding="utf-8")
    (dest / "examples" / ".gitkeep").write_text("", encoding="utf-8")
    print(f"created skills/{name}/  (SKILL.md, README.md, references/, examples/)")
    print("next: edit SKILL.md, then run  python scripts/verify.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
