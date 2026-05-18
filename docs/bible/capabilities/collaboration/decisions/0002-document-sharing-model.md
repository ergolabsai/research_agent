---
id: capabilities-collaboration-0002
title: Document sharing is an explicit grant, separate from workspace membership
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Users will need to share a single document with another user without inviting them into the entire workspace. The classic Google Docs / Notion pattern. The question is whether sharing is modeled as a special workspace-membership-of-one, or as a separate grant.

## Decision

A `DocumentShare` is a separate first-class entity: a grant of access from a document to a user, with its own access level (`view` | `edit`). Document shares are evaluated *in addition to* workspace membership during authorization checks.

The effective access of `principal` to `document` is the maximum of:

1. The principal's workspace-membership role (if the document lives in a workspace).
2. The principal's direct document share (if any exists).
3. "Owner" if the principal owns the document directly.

A document may be shared even if it does not live in a workspace (personal-scope documents are common).

## Consequences

**Easy:**
- Sharing one document is a one-row insert into `DocumentShare`. No workspace gymnastics.
- The authorization check is a single function: "given a principal and a document, what's the max access level across these three sources?"
- Revoking a share is a one-row delete. The user's other access (via workspace membership, etc.) is unaffected.

**Hard:**
- The authorization function has three input sources to merge. Worth keeping centralized in one helper to avoid drift.
- "Why does this user have access?" debugging requires checking all three sources, not one.

**Forecloses:**
- "Share with everyone in workspace X" as a shortcut — that is what workspace membership *is*. Use that.
- Link-based sharing without a known recipient. Possible later as a fourth source ("anyone with this token"), but explicitly a separate ADR if it arrives.

## Alternatives considered

- **Sharing modeled as workspace membership of a singleton workspace** — rejected. Forces every share to create a workspace, polluting the user's workspace list and complicating workspace queries.
- **Sharing replaces workspace membership** ("if you're in the workspace, the share is irrelevant") — rejected. Loses the explicit grant trail and makes "remove from workspace but keep this one document" impossible.
- **Sharing is encoded as a string-permission list on the document row** — rejected. Doesn't scale, doesn't support per-share metadata (timestamp, granted-by, expiration).

## Review trigger

- Demand for link-based or anonymous sharing — a separate fourth source in the authorization check, introduced as its own ADR.
- Demand for share *expiration* or *revocation policies* (e.g., "share until X date"). At that point `DocumentShare` grows fields, but the model holds.
- Performance: the three-source authorization check is hot. If it becomes the dominant database cost, denormalize the access check into a materialized table.
