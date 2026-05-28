---
id: architecture-0005
title: Principal flows through every use-case as the first argument
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The project will be invoked from multiple driving adapters: HTTP API, CLI, eventually browser extensions and document-suite connectors. Each adapter has its own authentication mechanism (JWT in HTTP, local token in CLI, OAuth in connectors). If authorization decisions live at the adapter boundary, each adapter must re-implement them. They will drift. Some path will quietly bypass a check.

The earlier known issue with `/users/search` having no auth requirement is a direct symptom of this: authorization scattered across adapters means the check is easy to miss when adding an endpoint.

## Decision

Every use-case takes a `Principal` value object as its **first positional argument**. Authorization is checked **inside the use-case body** using a shared `authz` helper, not at the adapter boundary.

```python
async def validate_paper(principal: Principal, cmd: ValidatePaperCommand) -> ValidationResult:
    authz.require(principal, Permission.VALIDATE_PAPER)
    ...
```

`Principal` carries identity, roles, and the source of authentication. It is constructed at the adapter boundary (the API parses it from a JWT; the CLI parses it from a local token; an internal scheduler synthesizes one with a `system` role).

## Consequences

**Easy:**
- All authorization logic lives in one place per use-case — the first one or two lines of the function body.
- Adding a new driving adapter is mechanical: parse the adapter's credentials into a `Principal`, hand off to the use-case. The adapter cannot accidentally bypass authz because the use-case insists on receiving a `Principal`.
- Audit logging hooks naturally onto the use-case entry point.
- The CLI is genuinely safe to ship: an admin command does not work just because a non-admin user has the binary, because the use-case checks the role.

**Hard:**
- Every use-case signature has a `principal` parameter, even for use-cases that don't *use* it. This is intentional — see *Corollary* below.
- Internal jobs (replay, batch backfill) cannot quietly bypass authz; they must construct a `Principal` with a `system` role. This is one extra line at every entry point.
- The `Principal` type becomes a load-bearing contract — changing its shape is a cross-cutting change.

**Forecloses:**
- "Internal scripts don't need auth." They do. They construct a system Principal.
- Adapter-level `@require_role` decorators on routes. The route never decides; it only constructs the Principal and hands off.

## Corollary

No use-case runs without a `Principal`. Even use-cases that perform no authz-gated work take the parameter (and may ignore it). Reason: audit trails. A use-case that ignores its `Principal` today may need to log "who triggered this" tomorrow, and the plumbing is already there.

## Alternatives considered

- **Authz at the adapter boundary** (FastAPI dependencies, Click middleware) — rejected. Each adapter would re-implement the check, and the checks would drift. This is the *current* state and the reason this ADR exists.
- **Middleware/decorator that injects `Principal` into use-cases implicitly** — rejected. Implicit injection hides the dependency. An agent reading a use-case must be able to see all its inputs from the signature.
- **A thread-local / contextvar holding the current principal** — rejected for the same reason: implicit, hard to reason about, breaks under async boundaries.
- **Pass a "subject" string only, derive permissions inside each use-case** — rejected. Conflates identity (who) with authorization (what they can do). Concentrating role resolution in `Principal` construction means there is one place where "what does this token mean?" is answered.

## Review trigger

- A use-case is found that does not take `Principal` (other than a deliberately-exposed unauthenticated endpoint like guest-try, which still constructs a `guest` Principal).
- Authorization complexity grows past a flat `Permission` enum — at that point a richer policy system (Casbin, Oso, OPA) may be warranted.
