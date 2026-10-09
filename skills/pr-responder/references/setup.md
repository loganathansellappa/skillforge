# Setup

The skill needs three things: a way to read and post on your host, a token or CLI
login, and slophound for the gate.

## 1. Pick how you talk to the host

Two options, use whichever you already have:

- A host CLI: `gh` for GitHub, `glab` for GitLab. These handle auth for you once
  you log in.
- Plain `curl` with a token. Use this for Bitbucket, or anywhere a CLI is not set
  up.

## 2. Authenticate

GitHub CLI:

```bash
gh auth login        # once per machine
```

GitLab CLI:

```bash
glab auth login      # once per machine
```

Token for `curl`: create a token on your host with pull-request read and write
scope, then put it in an environment variable. Keep it out of shell history and out
of version control:

```bash
export PR_TOKEN="$(cat ~/.secrets/pr.token)"
```

The gate never needs the token. Only the host calls in
[`hosts.md`](hosts.md) do, and they read it from the environment or the CLI.

## 3. Install slophound

```bash
pipx install slophound     # or: uv tool install slophound
```

With slophound on `PATH`, the gate strips generated punctuation and then lints the
result. Without it, the gate still strips punctuation and prints a note that the
lint was skipped, so posting is never blocked by a missing tool.

## 4. Quick check

```bash
echo "This is a plain, human sentence about the code." | python humanize.py
```

You should see the same sentence printed and exit code 0. If you feed it a draft
full of em dashes and buzzwords, it exits 3 with a short report of what to fix.
