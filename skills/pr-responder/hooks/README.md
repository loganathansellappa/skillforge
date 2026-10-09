# Optional enforcement hook

The skill runs `humanize.py` on every draft, but an instruction can be skipped. On
a host that supports `preToolUse` command hooks (Copilot CLI, Claude Code), this
optional hook makes the punctuation layer of the gate deterministic: it inspects
every shell call and denies a PR-comment post whose body still contains the
characters the gate strips (em or en dashes, curly quotes, an ellipsis character, a
non-breaking space, or an emoji). That text never passed `humanize.py`.

It covers the punctuation layer, not the wording layer. It does not run slophound
(too heavy for a per-call hook), so it does not catch AI-sounding phrasing. Install
it as a backstop, and still run the gate on every draft.

## What ships here

| File | Purpose |
| ---- | ------- |
| `slop-guard-hook.example.py` | `preToolUse` handler. Denies a PR-comment POST (GitHub, GitLab, Bitbucket) whose body contains generated punctuation. Deny-only, fail-open, stdlib only. |

## Try it offline

```bash
echo '{"toolName":"bash","toolArgs":{"command":"gh api repos/o/r/pulls/7/comments -f body=\"Great — done\""}}' \
  | python slop-guard-hook.example.py
# -> {"permissionDecision":"deny",...}

echo '{"toolName":"bash","toolArgs":{"command":"gh api repos/o/r/pulls/7/comments -f body=\"Good catch, added a TTL.\""}}' \
  | python slop-guard-hook.example.py
# -> {}
```

## Install (Copilot CLI example)

```bash
mkdir -p ~/.copilot/hooks
cp slop-guard-hook.example.py ~/.copilot/hooks/slop-guard-hook.py
```

Then register it as a `preToolUse` command hook in your host's hook config, matched
to shell tool calls, and run it fail-open (`python ~/.copilot/hooks/slop-guard-hook.py; exit 0`).
Restart the host so the hook reloads.

The hook never executes the command, makes no network call, and always exits 0, so
a failure degrades to "allow" rather than blocking your shell.
