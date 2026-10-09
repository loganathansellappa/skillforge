# Example: respond to comments on your PR

Fully fictional. You are on GitHub. A reviewer left two comments on PR 7 in
`acme/widget`.

## 1. List the open comments

```bash
gh api repos/acme/widget/pulls/7/comments
```

Two come back:

- `src/cache.py:40` by `rae`: "This cache never expires."
- `src/cache.py:71` by `rae`: "Typo in the log line."

## 2. Read the cited code and judge

- `src/cache.py:40` - confirmed, the store has no TTL. Valid.
- `src/cache.py:71` - confirmed, "recieved" is misspelled. Valid.

## 3. Fix, then draft replies

Add a TTL and a test, fix the spelling. Draft a reply for each and run it through
the gate:

```bash
echo "Good catch. Added a one minute TTL and a test for eviction." | python ../humanize.py
```

The gate prints the sentence and exits 0. A draft full of praise and an em dash
would exit 3 instead, so you would rewrite it to the plain version first.

## 4. Confirm, push, post, resolve

Show the user the drafts and `git diff --stat`. After they confirm, commit on the
PR branch, push, then:

```bash
gh api repos/acme/widget/pulls/7/comments -f body="Good catch. Added a one minute TTL and a test for eviction." -F in_reply_to=11
```

Resolve the two threads once their fixes are pushed.
