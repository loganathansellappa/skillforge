# Reading local source safely and quickly

rca-tracer works by reading source that is already on disk. This note describes
how to do that well with an agent's standard tools, and how to stay read-only.

## Tools you use

- **Open a file at a line.** View a specific `file:line` so you can quote it.
- **Search text across a repository.** Find where a log string, symbol, or error
  is defined and used. Prefer a fast code search if your agent has one.
- **Read a specific revision.** Use your version-control tool to read a file as of
  a commit or tag, so you trace the code that actually shipped. A read-only show
  of a path at a revision is safe, because it changes nothing on disk.

## Stay read-only

rca-tracer diagnoses. During a trace, do not:

- edit, format, or save files,
- build, run, or test the code,
- check out branches, reset, stash, or force anything,
- commit or push.

Reading a file, searching text, and showing a path at a revision are the only
actions a trace needs. If you believe a build or run is required to confirm a
cause, record that as an open question and let the human decide.

## Work from the symptom inward

1. Take the exact text from the symptom (the log line, the error, the assertion).
2. Search for that literal string first. It usually points to the line that
   emits it.
3. From there, read outward along the call path: who calls this, what values
   reach it, where they come from.
4. Record every file you open in the hop ledger, even the ones that turn out to
   be fine. A `PASSED` row is evidence too.

## Reading across repositories

When the path leaves one repository for another, use the repo map to find the
second repository, then continue the search there. If it is checked out on disk,
read it locally. If it is not, read it remotely through the host API, following
[remote-access.md](remote-access.md). Either way there is no need to clone. Do not
assume what an unread repository's
code does.

## Speed

- Search before you browse. One search beats opening ten files.
- Quote the few relevant lines, not whole files.
- Respect the budget: 8 hops or 30 reads. If you approach it, write down the best
  remaining lead and report.
