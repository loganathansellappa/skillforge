# Reading source from a remote repository

rca-tracer traces remotely. You do not need the repositories on your machine. It
reads the few files a trace needs straight from the Git host over HTTP: fetch one
file, list a directory, search code. No local copy is involved at all.

(If a repository does happen to be on disk, the tracer reads it locally instead,
which is faster and needs no token. See [local-read.md](local-read.md). That is a
convenience, not a requirement. Tracing never clones a repository: it only reads.)

Everything below stays read-only and keeps credentials out of output.

## Credentials: the rules that avoid most problems

- Use a **read-level** token. A trace never writes, so it never needs write scope.
- Read the token from an **environment variable** inside the HTTP call. Never
  paste it into chat, print it, echo it, or write it to a log or a file.
- If a file or response contains a secret or personal data, refer to it by name
  and location. Do not copy the value into output. (Same redaction rule as a
  local read.)

Name the variable whatever your host expects, for example `GIT_TOKEN`,
`GITHUB_TOKEN`, `GITLAB_TOKEN`, or `BB_TOKEN`. The skill does not require a
specific name, and your repo map records which host each repository lives on.

## How each host exposes a read

Each host exposes the three reads a trace needs: fetch one file, list a directory,
and search code. Use the HTTP tool your harness or shell provides. Replace the
`{{...}}` placeholders. Drop the ref parameter to read the default branch.

### GitHub (github.com or GitHub Enterprise)

```http
# Fetch one file (base64 in .content, or send the raw Accept header to get text).
GET https://api.github.com/repos/{{owner}}/{{repo}}/contents/{{path}}?ref={{ref}} HTTP/1.1
Authorization: Bearer ******
Accept: application/vnd.github.raw+json

###

# List a directory (returns an array of entries with name/path/type).
GET https://api.github.com/repos/{{owner}}/{{repo}}/contents/{{dirPath}}?ref={{ref}} HTTP/1.1
Authorization: Bearer ******

###

# Search code within one repo. Page with &page=; results are in .items.
GET https://api.github.com/search/code?q={{query}}+repo:{{owner}}/{{repo}} HTTP/1.1
Authorization: Bearer ******
```

For GitHub Enterprise, swap `api.github.com` for `{{host}}/api/v3`.

### GitLab (gitlab.com or self-managed)

```http
# Fetch one file (URL-encode the path; .content is base64).
GET https://{{host}}/api/v4/projects/{{projectIdOrPath}}/repository/files/{{encodedPath}}?ref={{ref}} HTTP/1.1
PRIVATE-TOKEN: ******

###

# List a directory (tree; page with &page=).
GET https://{{host}}/api/v4/projects/{{projectIdOrPath}}/repository/tree?path={{dirPath}}&ref={{ref}} HTTP/1.1
PRIVATE-TOKEN: ******

###

# Search code in one project.
GET https://{{host}}/api/v4/projects/{{projectIdOrPath}}/search?scope=blobs&search={{query}} HTTP/1.1
PRIVATE-TOKEN: ******
```

`{{projectIdOrPath}}` is the numeric project id, or the URL-encoded `group/repo`.

### Bitbucket Cloud (bitbucket.org)

```http
# Fetch one file (returns the raw bytes).
GET https://api.bitbucket.org/2.0/repositories/{{workspace}}/{{repo}}/src/{{ref}}/{{path}} HTTP/1.1
Authorization: Bearer ******

###

# List a directory (append a trailing slash; entries in .values, page with .next).
GET https://api.bitbucket.org/2.0/repositories/{{workspace}}/{{repo}}/src/{{ref}}/{{dirPath}}/ HTTP/1.1
Authorization: Bearer ******

###

# Search code across a workspace.
GET https://api.bitbucket.org/2.0/workspaces/{{workspace}}/search/code?search_query={{query}} HTTP/1.1
Authorization: Bearer ******
```

### Bitbucket Server / Data Center (self-hosted)

```http
# Fetch one file. Join lines[].text with newlines; page with start= until isLastPage.
GET https://{{host}}/rest/api/1.0/projects/{{project}}/repos/{{repo}}/browse/{{path}}?at={{ref}}&start={{start}}&limit=5000 HTTP/1.1
Authorization: Bearer ******

###

# List a directory (children.values; page with children.nextPageStart).
GET https://{{host}}/rest/api/1.0/projects/{{project}}/repos/{{repo}}/browse/{{dirPath}}?start={{start}}&limit=1000 HTTP/1.1
Authorization: Bearer ******

###

# Search code (drop project:/repo: to widen).
POST https://{{host}}/rest/search/latest/search HTTP/1.1
Authorization: Bearer ******
Content-Type: application/json

{"query": "{{query}} project:{{project}} repo:{{repo}}", "entities": {"code": {"start": 0, "limit": 25}}}
```

### Any other Git host

If the host has no read API listed above, read without a full checkout:

- `git archive --remote=<url> <ref> <path>` streams a single path over the
  protocol, with no working copy on disk.
- A blobless or treeless partial fetch (`git clone --filter=blob:none --no-checkout`,
  or `git fetch` with a partial filter) pulls only the objects a read touches,
  rather than the whole working tree. Use this only when `git archive` is
  unavailable, keep it read-only, and remove the temporary object store afterward.

## If a read fails

- **401 / 403:** the token is missing, wrong, or lacks read scope for that repo.
  Check the environment variable is set and persistent, then retry. Never echo it
  to confirm it is set, because a request is a safer test.
- **404 on a known path:** the ref or the path is wrong, or the path moved. Search
  for a stable anchor (a function name, an error string, a config key) and read
  the corrected path.
- **An HTML login page instead of file content:** you hit a browser `raw` URL.
  Use the REST file endpoint above, which honors the token.

## Budget accounting

Remote reads count against the same budget as local reads: 8 hops, 30 file reads.
One logical file read counts once even when the host makes you page it with
`start` / `page` / `next`. Each code search counts once. Re-reading the same file
later counts again.
