# Example: review a PR and post findings

Fully fictional. You were asked to review PR 12 in `acme/widget` on GitHub.

## 1. Read the diff

```bash
gh pr diff 12 --repo acme/widget
```

## 2. Write grouped findings

- Blocking: `src/auth.py:88` builds a SQL query with string formatting. Use a
  parameter.
- Worth fixing: `src/auth.py:120` swallows the exception with a bare `except`.
- Minor: `src/auth.py:12` imports a module it does not use.

## 3. Show the user first

Present all three. Post nothing yet. Ask which to post and whether each is inline
or general.

## 4. Gate each finding, then post

The user picks the blocking one as inline and the rest as general. Run each through
the gate:

```bash
echo "This builds the query from a formatted string. Pass the value as a parameter so it cannot be injected." | python ../humanize.py
```

After it passes, post the inline comment:

```bash
gh api repos/acme/widget/pulls/12/comments \
  -f body="This builds the query from a formatted string. Pass the value as a parameter so it cannot be injected." \
  -f commit_id=abc123 -f path=src/auth.py -F line=88 -f side=RIGHT
```

Review mode stops here. It posts comments and never changes the code.
