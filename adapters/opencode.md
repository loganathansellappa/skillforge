# Adapter: OpenCode

*Install format confirmed against the OpenCode docs on 2026-10-09. Re-check before
you rely on it, because formats change.*

OpenCode supports Agent Skills in the same `SKILL.md` format, and it also reads the
shared `.agents/skills/` and `.claude/skills/` locations, so a skillforge skill
works without conversion.

## Install locations

Global (all projects):

```
~/.config/opencode/skills/<skill-name>/SKILL.md
```

Project:

```
.opencode/skills/<skill-name>/SKILL.md
```

Also read by OpenCode (cross-tool compatibility):

```
.agents/skills/<skill-name>/SKILL.md
.claude/skills/<skill-name>/SKILL.md
```

## Copy a skill

```bash
cp -r skills/rca-tracer ~/.config/opencode/skills/
```

## Optional: expose it as a command

If you prefer a slash command, add a thin command file that points the agent at the
skill. Commands live in `~/.config/opencode/commands/` (global) or
`.opencode/commands/` (project), and the file name becomes the command.

```markdown
---
description: Trace a bug to its root cause with rca-tracer
---
Use the rca-tracer skill. Symptom: $ARGUMENTS
Follow the skill's method and output contract exactly.
```

Saved as `rca.md`, this gives you `/rca <symptom>`.

## Notes

- Copy the whole folder so `references/` and `examples/` resolve.
- Keep your filled-in `repo-map.md` and `layer-map.md` local.
