---
id: adapters-driven-0010
title: python-jose as the `TokenIssuer` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`TokenIssuer` ([port 0006](../../../ports/decisions/0006-token-issuer-port.md)) needs a JWT library. Mature Python options: `python-jose`, `pyjwt`, `authlib`. All handle HS256 competently. Differences: maintenance activity, ergonomics, support for advanced algorithms.

## Decision

Implement `TokenIssuer` with `JoseTokenIssuer` using `python-jose`. Access tokens signed with HS256, secret from `settings.secret_key`. Refresh tokens are opaque random strings stored server-side with their metadata (user_id, expires_at).

Current implementation lives in `backend/app/security.py`; the move to `adapters/driven/identity/jose_token_issuer.py` (or similar) is part of the migration.

## Consequences

**Easy:**
- python-jose is well-known; the implementation is short.
- HS256 with a strong secret is appropriate for first-party tokens.
- The port shape isolates the library choice; migrating to `pyjwt` or `authlib` later is an adapter swap.

**Hard:**
- python-jose's maintenance pace has varied over the years. Worth monitoring.
- HS256 means the secret key is shared across all verifiers. If a future service needs to verify tokens, asymmetric signing (RS256, EdDSA) becomes attractive — at that point an adapter change.

**Forecloses:**
- Nothing the port couldn't replace with a different adapter later.

## Alternatives considered

- **pyjwt** — viable. Closer-to-the-spec, less ergonomic for some edge cases. Equally good choice.
- **authlib** — more capable (full OAuth 2.0 stack) but more than needed for first-party JWT issuance.

## Review trigger

- python-jose maintenance becomes a concern (stale releases, unpatched CVEs).
- Asymmetric signing becomes necessary — write a new adapter ADR superseding this one.
