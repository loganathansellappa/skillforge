# layer-map.md (template)

Copy this file to `layer-map.md` and fill it in for your own system. Name your
layers and say which repositories and folders belong to each. The tracer uses
this to route a symptom to a starting layer and to recognise when the path
crosses a boundary. Keep this file local.

| layer | repositories (labels) | folders / notes |
| ----- | --------------------- | --------------- |
| client | web | src/pages, src/components |
| api | api | src/routes, src/middleware |
| service | service | src/domain, src/usecases |
| data | data | src/repositories, migrations |

Routing hints (optional but useful):

- A symptom seen in the browser usually starts at `client`.
- An HTTP error code usually starts at `api`.
- A wrong stored value usually starts at `service` or `data`.

The tracer still confirms the real starting point by reading source. These hints
only choose where to look first.
