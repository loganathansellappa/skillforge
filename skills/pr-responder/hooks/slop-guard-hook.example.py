#!/usr/bin/env python3
"""OPTIONAL preToolUse hook: enforce the pr-responder humanize gate at the tool layer.

This is an EXAMPLE, host-neutral enforcement hook for Copilot CLI / Claude Code and
any host that supports `preToolUse` command hooks. It is not required to use the
skill, and it is not wired in by default. The skill itself runs `humanize.py` on
every draft; an instruction can be skipped, so this hook is the deterministic
backstop for the part that can be checked without the agent's cooperation.

WHAT IT CHECKS (deterministic, host-neutral)
--------------------------------------------
pr-responder posts through the host CLIs (`gh`, `glab`, `curl`), so there is no
single wrapper script to route through. What a hook CAN check at the tool boundary
is the text being posted. When a shell call posts a PR comment (GitHub, GitLab, or
Bitbucket) and the comment body still contains the punctuation the gate strips -
em or en dashes, curly quotes, an ellipsis character, a non-breaking space, or an
emoji - the post is denied. That text never went through `humanize.py`, because the
sanitizer would have removed exactly those characters.

This covers the punctuation layer deterministically. It does not run slophound (too
heavy for a per-call hook), so it does not catch AI-sounding wording. Install it as
a backstop, not a replacement for running the gate.

FAIL BEHAVIOR
-------------
Always exits 0; allow/deny is expressed only in the JSON body. Anything not
positively identified as an ungated post is ALLOWED. Stdlib only; cross-platform;
no network; never executes the command.
"""
import json
import re
import sys

COMMENT_ENDPOINT = re.compile(
    r"(?i)(?:"
    r"pull-?requests?/[^/\s'\"]+/comments"
    r"|pulls/[^/\s'\"]+/comments"
    r"|issues/[^/\s'\"]+/comments"
    r"|merge_requests/[^/\s'\"]+/(?:notes|discussions)"
    r"|discussions/[^/\s'\"]+/notes"
    r")"
)
HTTP_CLIENT = re.compile(
    r"(?i)\b(curl|wget|Invoke-RestMethod|Invoke-WebRequest|iwr|irm|gh|glab)\b"
    r"|urllib\.request|requests\.(post|put|patch)|http\.client"
)
POSTISH = re.compile(
    r"(?i)(-Method\s+(POST|PUT|PATCH)|-X\s+(POST|PUT|PATCH)|--request\s+(POST|PUT|PATCH)"
    r"|\bPOST\b|\bPUT\b|\bPATCH\b|(^|[\s;&|])-d\b|--data|-Body\b"
    r"|requests\.(post|put|patch)"
    r"|(^|[\s;&|])-f\b|--field\b|--input\b|(^|[\s;&|])-F\b)"
)

# The exact characters the humanize gate's sanitize() removes. If the posted body
# still has any of them, it did not pass the gate.
GENERATED_PUNCT = re.compile(
    "[\u2014\u2013\u2018\u2019\u201c\u201d\u2026\u00a0]"          # dashes, quotes, ellipsis, nbsp
    "|[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF]"    # emoji + symbol ranges
)


def _emit(decision):
    sys.stdout.write(json.dumps(decision))
    sys.exit(0)


def allow():
    _emit({})


def deny(reason):
    _emit({"permissionDecision": "deny", "permissionDecisionReason": reason})


def read_payload():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _collect_strings(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, out)


def extract_command(payload):
    args = payload.get("toolArgs")
    if args is None:
        for key in ("toolArguments", "arguments", "args", "input"):
            if isinstance(payload.get(key), (dict, str)):
                args = payload[key]
                break
    if isinstance(args, dict):
        for k in ("command", "script", "cmd", "commandLine"):
            if isinstance(args.get(k), str) and args[k].strip():
                return args[k]
    if isinstance(args, str) and args.strip():
        return args
    collected = []
    _collect_strings(payload, collected)
    return "\n".join(collected)


def split_statements(cmd):
    return [s.strip() for s in re.split(r"&&|\|\||;|\n", cmd) if s.strip()]


def main():
    payload = read_payload()
    if not (payload.get("toolName") or payload.get("toolArgs") is not None
            or any(k in payload for k in ("toolArguments", "arguments", "command"))):
        allow()
    cmd = extract_command(payload)
    if not cmd:
        allow()

    for stmt in split_statements(cmd):
        is_post = (COMMENT_ENDPOINT.search(stmt) and HTTP_CLIENT.search(stmt)
                   and POSTISH.search(stmt))
        if is_post and GENERATED_PUNCT.search(stmt):
            deny(
                "slop-guard: this PR-comment body still contains punctuation the "
                "humanize gate removes (em/en dash, curly quote, ellipsis, nbsp, or "
                "emoji), so it did not pass the gate. Run the draft through the gate "
                "first, then post the cleaned text."
            )
    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        allow()
