# Contributing to skillforge

Thanks for improving skillforge. One rule matters more than all the others.

## Rule #1: no private or internal data

skillforge is **public**. Every file you add or edit must be free of:

- Company, product, team, or project **names**
- Internal **hostnames**, URLs, or network addresses (`*.internal`, `*.corp`,
  private IPs, `ssh://…`, `git@…`)
- **Personal paths** (`C:\Users\<you>`, `/home/<you>/…`)
- **Secrets**: tokens, keys, passwords, private keys
- Internal **ticket ids** (`ABC-1234`)
- Real **email addresses** (use `someone@example.com`)
- Real customer data, logs, or stack traces with identifiable content

Use **fictional** stand-ins everywhere: an app called *Acme Shop*, services
*web*/*api*/*worker*, hosts *example.com*, users *alice*/*bob*. Every example in
every skill must be invented, not redacted-from-real.

### The leak scanner enforces this

```bash
python scripts/leak_scan.py      # must print "PASS"
python scripts/verify.py         # full gate: leak scan + frontmatter + tests
```

Both run in CI on every push/PR. A finding fails the build.

### Enable the git hooks (recommended)

Enable the local hooks once per clone so the checks run before anything leaves
your machine:

```bash
git config core.hooksPath .githooks
```

`pre-commit` runs the leak scan, and `pre-push` runs the full gate. See
[.githooks/README.md](.githooks/README.md).

### Catching your own company's names locally

The scanner bakes in generic leak *classes* (paths, hosts, secrets, tickets…),
but it can't know your specific company/product names. Create a **local, never
committed** denylist so you catch them before they ship:

```
# scripts/company-terms.txt   (gitignored — do NOT commit)
Contoso
contoso-prod
MySecretProject
```

One term per line, `#` for comments. `scripts/company-terms.txt` is gitignored,
so your list never enters the public repo, and neither do the names on it.

## Adding a skill

```bash
python scripts/new_skill.py my-skill-name
```

This scaffolds `skills/my-skill-name/` with a `SKILL.md` (valid frontmatter),
`references/`, and `examples/`. Then:

1. Write the skill generically. Fictional examples only.
2. `python scripts/verify.py` until it's green.
3. Add adapter notes if the skill needs platform-specific install steps.
4. Open a PR. CI must pass.

## Skill shape

```
skills/<name>/
  SKILL.md            # YAML frontmatter (name, description) + the method
  references/         # templates & deep-dives the skill loads on demand
  examples/           # fully fictional worked examples
```

Frontmatter `name:` must equal the folder name. `description:` must say *when*
to use the skill (that's what platforms match on).

## License

By contributing you agree your work is released under the repo's MIT license.
