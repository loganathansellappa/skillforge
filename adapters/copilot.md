# Adapter: GitHub Copilot

*Install format confirmed against GitHub docs on 2026-10-09. Re-check before you
rely on it, because formats change.*

Copilot reads a skill from a folder containing `SKILL.md` with YAML frontmatter
(`name`, `description`). The `name` must be lowercase, hyphenated, and match the
folder. skillforge skills already follow this, so no conversion is needed.

## Install locations

Personal (available in all your projects):

```
~/.copilot/skills/<skill-name>/SKILL.md
```

Project (shared with everyone on the repo):

```
.github/skills/<skill-name>/SKILL.md
.agents/skills/<skill-name>/SKILL.md
```

## Copy a skill

```bash
cp -r skills/rca-tracer ~/.copilot/skills/
```

## Or use the GitHub CLI

`gh skill` (GitHub CLI v2.90+) can install directly from a repository:

```bash
gh skill install loganathansellappa/skillforge rca-tracer
```

Install from a local checkout:

```bash
gh skill install --from-local ./skills/rca-tracer
```

## Load and use

In Copilot CLI:

```
/skills reload          reload after adding a skill
/skills list            show loaded skills
/skills info rca-tracer show where it loaded from
```

Then describe your task. The skill activates when the request matches its
`description`, or you can invoke it by name.

## Notes

- The whole skill folder matters, not just `SKILL.md`. Copy `references/` and
  `examples/` along with it so on-demand files resolve.
- Keep your filled-in `repo-map.md` and `layer-map.md` local to your machine.
