---
id: capabilities-identity-0003
title: Role-based authorization; no policy engine yet
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Authorization complexity grows along a continuum:

- Hard-coded role checks (`if principal.role == "admin"`).
- A static role-to-permission map with `Permission` enums.
- A policy engine that evaluates arbitrary expressions (Casbin, Oso, OPA).
- ABAC (attribute-based): policies over user attributes, resource attributes, environment, time, etc.

Each step adds expressiveness and operational complexity. The right step is "as complex as you need, no more."

## Decision

The system uses **role-based authorization with a flat `Permission` enum and a static role→permissions map**:

- `Principal` carries one or more `Role` values (a small enum: `user`, `admin`, `dev`, `guest`, `system`).
- `Permission` is a flat enum (`VALIDATE_PAPER`, `MANAGE_WORKSPACE`, `ADMIN_RESET_JOBS`, etc.).
- A static map declares which roles have which permissions.
- A use-case calls `authz.require(principal, Permission.X)` at its entry; the helper looks up whether *any* of the principal's roles grants `X`.

Resource-level checks (e.g., "this principal owns *this* document") are performed *in addition* to the permission check, inside the use-case, using repository lookups.

## Consequences

**Easy:**
- The complete authorization model is readable in one file. Adding a permission is one line; granting a role a new permission is one line in the map.
- The model is statically inspectable: an audit can list all permissions and all roles that grant them by reading code, not running a policy engine.
- No new framework dependency.

**Hard:**
- Resource-level rules ("you can edit the document if you own it") are *not* expressed in the role map; they live inside each use-case. This is fine — they belong with the domain logic — but it means "what can this user do?" is not answered by inspecting roles alone.
- Cross-cutting policies (e.g., "no actions are allowed during scheduled maintenance") would have to be threaded by hand. Acceptable at current scale.

**Forecloses:**
- Declarative attribute-based rules ("anyone in the same workspace can edit"). These are expressible as use-case logic today; that is the intended pattern.

## Alternatives considered

- **Casbin / Oso / OPA from the start** — rejected. A policy engine becomes valuable when (a) rules change without code deploys, or (b) the rule set is large enough that a code-centric expression sprawls. Neither is true yet.
- **Hard-coded `if principal.role == "admin"` checks** — rejected. Inverts the relationship: the use-case asks about roles, not permissions. Adding a permission would require touching every use-case that grants it.
- **Per-user permission lists (no roles)** — rejected. Roles are how humans think about access; granting permissions directly per user does not scale.

## Review trigger

- Authorization rules need to change without code deploys (e.g., admins toggling feature access for specific accounts).
- The role→permission map grows past ~50 permissions and becomes hard to reason about as a flat table.
- A genuinely attribute-based rule appears that does not fit cleanly inside any use-case (cross-cutting concern). Reconsider a policy engine then.
