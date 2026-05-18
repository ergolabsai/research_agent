---
id: ports-0007
title: `PasswordHasher` port for credential hashing
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Password hashing is a small but security-critical primitive. The algorithm matters (bcrypt → argon2id is a defensible upgrade path), the parameters matter (work factor / time cost), and the *library* matters less.

Today, bcrypt is called directly from `security.py`. A port lets the core require "a hasher" without binding to a library or algorithm.

## Decision

```python
class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...
    async def verify(self, password: str, hashed: str) -> bool: ...
    async def needs_rehash(self, hashed: str) -> bool: ...
```

`needs_rehash` returns `True` when the stored hash was produced with old parameters (or an old algorithm). The login use-case calls it after successful verify and, if true, recomputes the hash and updates the user record. This makes algorithm/parameter migration safe and online.

## Consequences

**Easy:**
- Algorithm migration (bcrypt → argon2id) is an adapter change. The `RegisterUser` and `Login` use-cases do not change. Existing users transparently re-hash on next login.
- Test adapter does plain comparison (clear-text), suitable for unit tests where the hash logic is not under test.

**Hard:**
- `verify` is intentionally slow (the whole point of password hashing). Tests against real hashes are slow. Use the fake adapter for unit tests; reserve the real adapter for integration tests.

**Forecloses:**
- Direct `bcrypt` or `argon2-cffi` imports outside the adapter.
- Per-user hash-algorithm fields stored alongside the user (the `needs_rehash` discriminant is computed from the hash string, which carries its own algorithm identifier in standard formats).

## Adapters

- **`BcryptPasswordHasher`** — current. work factor from settings (default 12).
- **`Argon2PasswordHasher`** — future. argon2id with reasonable defaults.
- **`PlainTextHasher`** — test fake. Stores the password as-is. Never used in production.

See [adapters/driven/decisions/0011-bcrypt-password-hasher.md](../../adapters/driven/decisions/0011-bcrypt-password-hasher.md).

## Review trigger

- An argon2id migration is undertaken — write a follow-up adapter ADR and let `needs_rehash` carry the migration.
- Industry guidance shifts (NIST or OWASP recommendations change). The port lets the adapter follow without disruption.
