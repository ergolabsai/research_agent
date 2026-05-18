# Driving adapters

The user-facing surfaces of the system. Each is a translation layer between an external invocation idiom (HTTP, CLI, browser events) and the use-case layer.

## Adapters in this folder

| Adapter | Purpose | Status |
|---|---|---|
| [FastAPI HTTP API](./decisions/0001-fastapi-for-http.md) | HTTP/JSON interface used by the React frontend and any HTTP client. | accepted |
| [Typer CLI](./decisions/0002-typer-for-cli.md) | The CLI binary. First-class adapter per [architecture/0007](../../architecture/decisions/0007-cli-first-driving-adapter.md). | accepted |
| [React + MUI frontend](./decisions/0003-react-mui-for-web.md) | The web UI. A driving adapter that calls the HTTP API. | accepted |

## Conventions all driving adapters follow

1. **Construct `Principal` at the boundary.** Each adapter has a mechanism to turn its credentials into a `Principal` value object. The use-case receives it as the first argument.
2. **No business logic.** Parse input, call a use-case, format output. If the adapter is doing more, push it down into a use-case.
3. **Errors are translated, not swallowed.** A use-case raises a typed exception (e.g., `PermissionDenied`); the adapter maps it to an HTTP status, CLI exit code, or UI alert. The translation table lives in the adapter.
4. **`--json` mode for agent-friendly output.** The CLI must support it on every command; the API is JSON-native. The frontend is exempt — it is for humans.
5. **No driven-adapter imports.** A driving adapter cannot import from `adapters/driven/`. Going through composition is the path.

See the individual ADRs for adapter-specific conventions.
