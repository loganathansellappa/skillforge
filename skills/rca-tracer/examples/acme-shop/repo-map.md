# repo-map.md (Acme Shop, fictional)

The tracer reads these remotely through the host API, so none of them need to be
on disk. With no `ref` column the tracer reads the default branch. Add a `ref`
column to pin a branch or tag. The read token lives in an env var, not in this
file.

| label | location | contains |
| ----- | -------- | -------- |
| web | github:acme-shop/web | browser client: cart, checkout pages |
| api | github:acme-shop/api | HTTP API: order endpoints, auth |
| service | github:acme-shop/service | order and pricing logic |
| data | github:acme-shop/data | database access, order schema |
