# Hosts

The method is the same on every host: list the open comments, read the cited code,
draft a reply, run it through the gate, then post after the user confirms. Only the
commands differ. Pipe every draft through the gate first:

```bash
reply="$(echo "$draft" | python <skilldir>/humanize.py)" || { echo "rewrite it"; exit 1; }
```

The `|| exit` matters: when the gate rejects a draft it exits 3, so the post never
runs on text that failed.

## GitHub (`gh`)

```bash
# List review comments (inline) and issue comments (general)
gh api repos/{owner}/{repo}/pulls/{pr}/comments
gh api repos/{owner}/{repo}/issues/{pr}/comments

# Reply to a review comment thread
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f body="$reply" -F in_reply_to={comment_id}

# New inline comment (needs the head commit sha)
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f body="$reply" -f commit_id={sha} -f path={file} -F line={n} -f side=RIGHT

# New general comment
gh api repos/{owner}/{repo}/issues/{pr}/comments -f body="$reply"
```

Resolving a thread is a GraphQL call (`resolveReviewThread`) that takes the thread
id, not the comment id. Fetch the thread id first, then:

```bash
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id={thread_id}
```

## GitLab (`glab` or `curl`)

```bash
# List merge-request discussions
glab api projects/{id}/merge_requests/{iid}/discussions

# Reply in a thread
glab api -X POST projects/{id}/merge_requests/{iid}/discussions/{discussion_id}/notes \
  -f body="$reply"

# New general note
glab api -X POST projects/{id}/merge_requests/{iid}/notes -f body="$reply"

# Resolve a thread
glab api -X PUT "projects/{id}/merge_requests/{iid}/discussions/{discussion_id}?resolved=true"
```

An inline note uses `POST .../discussions` with a `position` object (base and head
sha, old and new path, and the line).

## Bitbucket (`curl`)

Bitbucket Cloud:

```bash
# List comments
curl -H "Authorization: Bearer $PR_TOKEN" \
  https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{pr}/comments

# Reply (set parent.id); inline adds an "inline" object with path and "to"
curl -H "Authorization: Bearer $PR_TOKEN" -H "Content-Type: application/json" \
  -X POST https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{pr}/comments \
  -d "{\"content\":{\"raw\":\"$reply\"},\"parent\":{\"id\":{comment_id}}}"
```

Bitbucket Server and Data Center use `/rest/api/1.0/projects/{proj}/repos/{slug}/pull-requests/{pr}/comments`
with a `parent.id` for replies and a `state: RESOLVED` update to resolve.

## One rule for all of them

Whatever host you use, the draft goes through the gate before it reaches any of
these commands. The gate is the point of the skill, and it runs the same way
everywhere.
