---
id: architecture-0008
title: One CLI binary, role-gated commands
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The CLI ([0007](./0007-cli-first-driving-adapter.md)) must serve two audiences:

- **End users** — paper validation, job listing, workspace management.
- **The team** — admin operations (reset jobs, replay a run, dump a trace) and dev-only commands during development.

A naive split is to ship two binaries: `advisor` for users and `advisor-internal` for the team. This sounds safer but creates parallel build pipelines, parallel docs, divergent flag conventions, and a constant question of "which binary do I run?"

The pattern used by `gh`, `aws`, `kubectl`, `stripe`, and `claude` is different.

## Decision

There is **one** `advisor` binary. Command visibility and authorization are gated by:

1. **Server-side authorization** — the real security boundary. Admin operations require an admin-role JWT/token. The CLI cannot bypass this by being run by anyone.
2. **Local visibility flags** — `--help` hides admin commands from non-admin principals, and hides dev commands unless `ADVISOR_DEV=1` (or the principal carries a `dev` role).

The surface looks like:

| Command group | Audience | Gate |
|---|---|---|
| `advisor validate`, `advisor jobs`, `advisor papers`, `advisor workspace`, `advisor share` | End users | Server-side authz: logged-in user, ownership/membership checks. |
| `advisor config`, `advisor login`, `advisor logout` | Everyone | Local-only, no gate. |
| `advisor admin *` | Team | Hidden from `--help` for non-admins; server requires `role=admin` token. |
| `advisor dev *` (replay-job, dump-trace, eval-agent, etc.) | Team during development | Registered only if `ADVISOR_DEV=1` env var is set OR principal has `dev` role. |

A separate `advisor-internal` binary is reserved for *true* ops scripts that we genuinely do not want shipped to user machines at all (rotate keys, seed test data, run migrations against production). It is not a parallel of `advisor`; it is a small, narrow tool.

## Consequences

**Easy:**
- One install, one update mechanism, one docs site, one release pipeline.
- Admins use the same binary as users — no context-switching, no "which binary has the new feature?"
- Hiding by role is a UX feature, not a security feature. The security feature is server-side authz, which works regardless of binary.

**Hard:**
- The CLI must understand its caller's role to render help text correctly. This means the CLI looks up the principal's role at startup (a server call, cached locally) — adding a small dependency on the server being reachable for help text.
- Mitigation: help text degrades gracefully offline (shows the "user" command subset).

**Forecloses:**
- Build-time stripping of commands. Tempting ("just don't compile admin commands into the user binary") but turns the binary into multiple binaries with different code paths — exactly what this decision rules out.
- Treating CLI command visibility as a security boundary. It is not. The server is.

## Alternatives considered

- **Two binaries (`advisor`, `advisor-internal`)** — rejected as default. Duplicates everything. Use this pattern only for the narrow class of true ops scripts mentioned above.
- **Single binary, no visibility hiding** — viable; less polished. Users see admin commands in `--help` and get a permission error if they try them. Acceptable, but the hidden-by-default experience is friendlier.
- **Plugin architecture (`advisor` core + dynamically-loaded admin plugins)** — rejected. Overkill for current scale. A future option if the surface grows past ~30 commands.

## Review trigger

- A class of internal command appears that is genuinely too dangerous to expose to a stolen-token attacker even with server-side authz (e.g., commands that operate on raw key material). Move those into the narrow `advisor-internal` binary.
- The number of commands grows past what is reasonable for a single binary's help text to organize (~30+). At that point a sub-command grouping refactor — or plugin architecture — becomes warranted.
