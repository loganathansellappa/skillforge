# rca-tracer

Root-cause analysis for a code defect across one or many repositories, local or
remote.

## What it solves

You have a symptom: an error, a wrong result, a crash, a failing test, a user
report. You need to know which line of code causes it, and the cause may live in
a different repository or layer than the one showing the problem. rca-tracer
follows the code path from the symptom to the responsible `file:line`, records
every step, and reports the cause with citations. It reads source remotely from a
Git host (GitHub, GitLab, Bitbucket, any host) with a read-level token, so you do
not need the repositories on your machine. If a repository is already on disk, it
reads that directly. When the trail leaves code it can read, it says so and stops.

It is read-only. It diagnoses, and it does not clone, edit, build, or run anything.

## Setup

1. Install the skill for your platform (see the repo root
   [README](../../README.md), section "Install").
2. Copy the two config templates and fill them in for your system:
   - `references/repo-map.template.md` to `repo-map.md`
   - `references/layer-map.template.md` to `layer-map.md`
   Keep these local. They name your repositories, so do not commit them here.
3. Make the repositories readable. For each one, put a remote coordinate (host +
   `owner/repo`) in your repo map and set a read-level token in the environment, so
   the tracer reads it through the host API. No clone or checkout is needed. A
   repository already on disk can instead use its local path, which the tracer
   reads directly with no token. See `references/remote-access.md` for host
   endpoints and token rules.

## Usage

Point your agent at the skill and give it a symptom. For example:

```
Use rca-tracer. Symptom: "orders over 1000 units are saved with quantity 0".
Repos are in my repo-map.md.
```

The skill routes the symptom to a starting layer, finds a concrete `file:line`
that matches it, traces hop by hop toward the origin, and returns a report with a
root cause (or an honest boundary), a trace, a certainty rating, and up to three
fix options for you to choose from.

A fully worked, fictional example is in [examples/acme-shop/](examples/acme-shop/).

## How it stays honest

- **Evidence Gate:** no claim without a `file:line` that was actually read.
- **Five guards** before it will call anything a root cause.
- **Budget** of 8 hops or 30 reads, then it reports what it has instead of
  guessing.
- **Redaction:** secrets and personal data are referred to by location, never
  copied into output.
