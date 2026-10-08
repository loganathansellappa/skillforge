# Adapter: Claude

*Install format confirmed against the Agent Skills spec on 2026-10-09. Re-check
before you rely on it, because formats change.*

Claude Agent Skills use the same shape skillforge already follows: a folder with
`SKILL.md` and YAML frontmatter. Required fields are `name` (lowercase, hyphens,
1 to 64 characters, matching the folder) and `description` (1 to 1024 characters,
stating what the skill does and when to use it).

## Install locations

User scope (all projects):

```
~/.claude/skills/<skill-name>/SKILL.md
```

Project scope (shared on the repo):

```
.claude/skills/<skill-name>/SKILL.md
```

## Copy a skill

```bash
cp -r skills/rca-tracer ~/.claude/skills/
```

## Use

Claude discovers the skill from its frontmatter and activates it when your request
matches the `description`. No extra registration step is required beyond placing
the folder.

## Notes

- Copy the whole folder, including `references/` and `examples/`, so the links in
  `SKILL.md` resolve.
- `rca-tracer` is read-only by design. If you use Claude's `allowed-tools`
  frontmatter field, you can restrict it to read and search tools to match that
  intent. This is optional.
- Keep your filled-in `repo-map.md` and `layer-map.md` local.
