---
id: capabilities-collaboration-0001
title: Workspace membership model — owner, editor, viewer
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A workspace must support multiple users with different levels of access. Several models are possible: a flat "member" role with all-or-nothing access; a role hierarchy with explicit per-role permissions; or a capability-based system where each member has a list of granted actions.

The cost of getting this wrong is high — once users start relying on a model, changing it requires careful migration of every existing workspace.

## Decision

Workspaces have three roles, in a strict hierarchy:

- **Owner** — exactly one per workspace. Created at workspace creation. Can do everything: manage members, change name, delete the workspace.
- **Editor** — can create, update, and delete documents within the workspace. Cannot manage members or the workspace itself.
- **Viewer** — read-only access to all documents in the workspace.

Membership is modeled as a join table (`WorkspaceMember`) with `user_id`, `workspace_id`, and `role`. Lookups are by either side.

Ownership transfer is supported as a single explicit action (`TransferWorkspaceOwnership`) — not by deleting the owner role. The previous owner becomes an editor.

## Consequences

**Easy:**
- The check "can this user X this workspace?" is a single role lookup + a small role-to-permission map. Cheap and obvious.
- Three roles cover the realistic needs of small teams without forcing users to think about capabilities.
- Adding a new role is a backwards-compatible change as long as it slots into the existing hierarchy (e.g., a future "commenter" between viewer and editor).

**Hard:**
- "Per-document overrides within a workspace" is *not* supported by this model. A workspace editor edits every document; a viewer reads every document. Per-document granularity uses [document sharing](./0002-document-sharing-model.md) on top.
- Role-to-permission mapping is hard-coded today. If permissions become finer-grained, this map will sprawl — but that is a tractable refactor.

**Forecloses:**
- A flat "member" role. The role distinction is the whole point.
- Multiple owners. Ownership is singular by intent — accountability and operations like "delete workspace" require an unambiguous owner.

## Alternatives considered

- **Flat "member" role, all-or-nothing access** — rejected. Too coarse; viewer mode is a real use case (sharing a workspace with a reviewer who shouldn't edit).
- **Capability-based (each member has a list of granted actions)** — rejected as default. Over-engineered for small teams. Reconsider only if enterprise-tier access requirements appear.
- **Two roles (owner + member)** — viable; close to the current state. Three was chosen because viewer-only is a common-enough need that conflating it with editor causes problems.

## Review trigger

- A real customer requests per-document permission overrides within a workspace beyond what document sharing supports.
- Enterprise-tier requirements (groups, inherited roles, audit policies) make capability-based access genuinely necessary.
- Role count grows past five — at that point a flat list of role names is harder than a structured permission model.
