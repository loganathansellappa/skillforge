# repo-map.md (template)

Copy this file to `repo-map.md` and fill it in for your own system. List every
repository the tracer may need. By default the tracer reads each repository
remotely through the host API, so you do not need it on disk. If a repository is
already checked out, give its local path instead. Keep this file local. It names
your repositories, so do not commit it back to a public repo.

One row per repository. Give a remote coordinate for the normal case, or a local
path when the repository is already on disk. A repository with both is read
locally first.

| label | location | contains |
| ----- | -------- | -------- |
| web | github:acme/web | browser client: pages, components, client-side state |
| api | github:acme/api | public HTTP API: request handling, auth, routing |
| service | gitlab:acme/service | business logic and orchestration |
| data | /path/to/data | database access, schema, migrations (already on disk) |

Column meanings:

- `label` is a short name you will use in the trace and in the layer map.
- `location` is where the tracer reads the repository from. Use a remote
  coordinate (the default, no clone needed) or a local path:
  - `github:owner/repo` (or `ghe:host/owner/repo` for GitHub Enterprise)
  - `gitlab:group/repo` (or with a host for self-managed)
  - `bbcloud:workspace/repo` (Bitbucket Cloud)
  - `bbserver:PROJECT/repo` (Bitbucket Server / Data Center)
  - any other Git host: give the repository URL
  - `/path/to/repo`: a local checkout, read directly with no token
- `contains` is one line so the tracer can route a symptom to the right place.
- Add a `ref` column if you trace against a specific branch, tag, or commit.
- For remote repositories, record which env var holds the read token (for example
  `token: GITHUB_TOKEN`) rather than the token value. See
  [remote-access.md](remote-access.md). Never write a token into this file.
