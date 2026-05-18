---
id: capabilities-identity-0002
title: Guest "try" flow with ephemeral Principal
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A new user should be able to validate a paper without first creating an account. The friction of "register before you can see what this thing does" is high; users bounce. But anonymous, fully unauthenticated access has its own problems: no rate limiting per user, no way to associate a result with a session, no path to "claim this guest session as my account."

## Decision

A **guest** is a real `Principal` constructed from a server-issued ephemeral token. The flow:

1. User clicks "Try without signing up."
2. Server creates a `User` row with a marker (`is_guest=True`), no password, and a randomly-generated identifier.
3. Server issues access + refresh tokens for that guest user.
4. The principal carries `role=guest` and `is_guest=True`.

Guest users can do most things a registered user can do (validate papers, view their own results), but a flat allow-list of permissions controls which use-cases are reachable. Admin and dev commands are not in that allow-list; neither is workspace sharing (since there is no one to share with).

A guest session can be "claimed" by completing registration: the user fills in email + password, and the existing guest `User` row is updated with credentials and `is_guest=False`. All prior work transfers seamlessly.

## Consequences

**Easy:**
- Zero-friction first run. Users see the product before committing.
- Guest users exist in the same `User` table as registered users — no parallel "session" type. Everything that takes a `Principal` works for both.
- Guest sessions can be reaped on a schedule: any `User` with `is_guest=True` and `last_active_at` older than N days can be deleted. (Reap policy is operational, separate ADR if needed.)
- Claiming a session is a single-row update plus token re-issuance. The user keeps their work.

**Hard:**
- The `User` table mixes registered and guest users. Queries that mean "real users" must filter `is_guest=False`. Mitigation: a `User.active_registered_users()` repository method that does this filtering once.
- Storage cost: every guest run creates a row. Reaping is necessary; without it, the table grows unbounded.
- Sharing edge cases: if a guest creates a document and another user tries to share with them, what is "them" before registration? Answer: sharing with guests is not supported. Guests can only own things; they cannot be the recipients of shares from others.

**Forecloses:**
- Truly anonymous, server-stateless validation (no user row, no token). The session model is built on the `User`-row identity; anonymous would require a parallel path.

## Alternatives considered

- **Anonymous endpoints without session tracking** — rejected. No way to rate-limit per user; no path to claim a session.
- **Local-only guest state in the browser (no server row)** — rejected. Validation jobs are server-side; the job needs an owner. Worth revisiting only if validation becomes a client-side computation, which is unlikely.
- **A separate `GuestSession` table parallel to `User`** — rejected. Doubles the principal-construction code paths and makes "claim this guest" a cross-table operation.

## Review trigger

- Guest abuse becomes a real cost (papers submitted purely to consume API quota). At that point: stricter rate limits per guest, captcha on guest issuance, or removal of the guest flow entirely.
- A real product requirement to share with guests appears — rare, but possible.
