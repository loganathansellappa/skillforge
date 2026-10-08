# Git hooks

These hooks stop private data or a broken gate from ever leaving your machine.
They are the local counterpart to the CI check in `.github/workflows/validate.yml`.

| Hook | Runs | Blocks when |
| ---- | ---- | ----------- |
| `pre-commit` | `scripts/leak_scan.py` | any private/internal data is found |
| `pre-push` | `scripts/verify.py` | leak scan, frontmatter, or tests fail |

## Enable them

Git does not run a repo's hooks until you point it at them (this is a safety
feature, since hooks are code). Enable them once per clone:

```bash
git config core.hooksPath .githooks
```

On macOS and Linux, make them executable:

```bash
chmod +x .githooks/pre-commit .githooks/pre-push
```

On Windows, Git for Windows runs these `sh` scripts as-is, so no extra step is
needed.

## Bypass (rarely, and know why)

```bash
git commit --no-verify     # skip pre-commit
git push --no-verify       # skip pre-push
```

CI still runs the full gate, so a bypass only defers the check rather than
skipping it.

## If a term is wrongly flagged

The leak scan can catch a company term you listed in `scripts/company-terms.txt`
(gitignored). That is working as intended. If a generic pattern misfires, adjust
the example to use a clear placeholder (`example.com`, `127.0.0.1`, `ABC-123`).
