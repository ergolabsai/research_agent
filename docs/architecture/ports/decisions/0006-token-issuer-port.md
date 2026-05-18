---
id: ports-0006
title: `TokenIssuer` port for JWT mint and verify
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

JWT minting and verification touches cryptography, key management, and time. The core needs to *use* tokens — issue them at login, refresh them, decode them into a `Principal`'s claims — but should not import a JWT library directly. The library choice (`python-jose`, `pyjwt`, `authlib`) is an adapter concern; the algorithm (HS256 → EdDSA, possibly) is too.

## Decision

```python
class TokenClaims(BaseModel):
    sub: str
    email: str
    roles: list[str]
    is_guest: bool = False
    iat: datetime
    exp: datetime

class TokenIssuer(Protocol):
    async def mint_access_token(self, claims: TokenClaims) -> str: ...
    async def mint_refresh_token(self, user_id: UserId) -> RefreshToken: ...
    async def verify_access_token(self, token: str) -> TokenClaims: ...
    async def verify_refresh_token(self, token: str) -> RefreshToken | None: ...
    async def revoke_refresh_token(self, token_id: str) -> None: ...
```

`RefreshToken` is a contract type carrying `token: str`, `token_id: str`, `user_id: UserId`, `expires_at: datetime`. The refresh side is stateful — the adapter is responsible for persisting refresh tokens (typically in the same `JobStore`/SQLite that backs everything else) and revoking them on use (rotation).

`verify_access_token` raises a typed `InvalidToken` / `ExpiredToken` exception on failure rather than returning `None` — the failure mode is meaningful to the caller.

## Consequences

**Easy:**
- The login use-case asks `TokenIssuer.mint_access_token(...)` and `mint_refresh_token(...)`. The refresh use-case asks `verify_refresh_token` then `mint_*` again. No JWT library imports outside the adapter.
- Algorithm migration (HS256 → EdDSA) is an adapter change. The port stays the same.
- Test adapter mints predictable tokens, useful for end-to-end tests.

**Hard:**
- The refresh-token-rotation contract is implicit in the call sequence (`verify_refresh_token` then `mint_refresh_token` invalidates the previous). The adapter must atomically revoke-and-issue; the port does not yet express this atomically. If this becomes a bug source, introduce a `rotate_refresh_token(old) -> new` method.

**Forecloses:**
- Direct `python-jose` or `pyjwt` use anywhere in core.

## Adapters

- **`JoseTokenIssuer`** — current. python-jose, HS256, secret key from settings. Refresh tokens persisted via a `RefreshTokenStore` (today an inlined SQL helper; will move to a method on `JobStore` or its own port).
- **`FakeTokenIssuer`** — test. Tokens are JSON-encoded claims with a fixed prefix; verification just parses them.

See [adapters/driven/decisions/0010-jose-token-issuer.md](../../adapters/driven/decisions/0010-jose-token-issuer.md).

## Review trigger

- Move to asymmetric signing (RS256, EdDSA) — e.g., when other services need to verify tokens without the secret key.
- Refresh-token rotation race conditions show up in practice. Introduce atomic rotation.
- Token revocation lists (for compromised tokens before they expire) become necessary. Add a `revoke_access_token(jti)` method backed by a short-TTL store.
