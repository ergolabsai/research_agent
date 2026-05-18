---
id: capabilities-identity-0001
title: JWT access tokens + rotating refresh tokens
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The system needs a session model that works across HTTP, CLI, and (eventually) connectors. Several patterns are common:

- Server-side sessions (a session row in the DB; client carries a session id). Stateful, requires lookup per request.
- JWT-only (client carries a self-contained signed token). Stateless, but revocation is hard.
- JWT access + refresh tokens (short-lived JWT + long-lived refresh, refresh-on-rotation). Mostly stateless with a small stateful escape hatch.

The third pattern is widely used (it is what most OAuth-style APIs effectively implement) and balances simplicity against the realistic need to revoke a compromised session.

## Decision

Two token types:

- **Access token** — a JWT, HS256-signed, 15-minute expiry. Carries `sub` (user id), `email`, `roles`, and any claims needed for `Principal` construction without a DB lookup. Verified cryptographically per request.
- **Refresh token** — opaque, server-stored, 7-day expiry. Used to mint a new access token. **Rotated on each use**: a successful refresh issues a new refresh token and invalidates the old one. Stored client-side as an HTTP-only cookie (API) or in a local file (CLI).

A successful login issues both. Logout revokes the refresh token (deletes the server-side row).

## Consequences

**Easy:**
- The hot path (every authenticated request) is cryptographic verification, no DB lookup. Fast.
- Compromised access tokens self-expire in 15 minutes.
- Compromised refresh tokens are detectable: if an attacker uses a refresh token, the original holder's next refresh fails (rotation invalidated their copy), and the system can react.
- The CLI's stored token works the same way; no special-case session model.

**Hard:**
- Two artifacts must be managed correctly. Bugs in rotation or revocation are easy to introduce; need integration tests for the full login → refresh → logout cycle.
- Refresh rotation requires the server to track refresh-token state — a small departure from "fully stateless." Acceptable.
- HMAC keys (`SECRET_KEY`) must be properly managed. Rotation requires care.

**Forecloses:**
- Truly stateless authentication. The refresh side is stateful by necessity.
- Per-token granular revocation of access tokens without compromising performance. (Acceptable: 15-minute expiry bounds the blast radius.)

## Alternatives considered

- **Server-side sessions only** — viable, simpler. Adds one DB lookup per request. Rejected because it limits horizontal scalability and adds a hot DB path.
- **JWT only, no refresh** — rejected. Long-lived JWTs cannot be revoked without an external blacklist; short-lived JWTs without refresh force re-login every 15 minutes.
- **OAuth 2.0 with PKCE for first-party clients** — viable; closer to industry standard. Rejected as initial implementation: the overhead of running an OAuth-grant flow for first-party CLI/web is larger than the benefit. Reconsider when third-party clients enter the picture.

## Review trigger

- A first third-party client (browser extension, partner integration) needs to authenticate. OAuth 2.0 + PKCE becomes warranted at that point; the JWT + refresh model can be wrapped to serve as the underlying token machinery.
- A real session-revocation requirement (legal hold, compromised account procedure) demands stronger guarantees than 15-minute access-token expiry.
- Cryptographic best practice shifts (e.g., HS256 → EdDSA recommended) — a key-rotation ADR follows.
