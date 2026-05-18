---
id: adapters-driven-0011
title: bcrypt as the `PasswordHasher` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`PasswordHasher` ([port 0007](../../../ports/decisions/0007-password-hasher-port.md)) needs an implementation. The two industry-accepted choices today are **bcrypt** and **argon2id**. Both are secure when configured properly. The trade-off:

- **bcrypt** — older, well-understood, widely deployed, ubiquitous in Python.
- **argon2id** — newer, OWASP's current first recommendation, more parameters to tune (memory cost, parallelism), better resistance to GPU-based attacks.

For a first-party password system with reasonable work-factor configuration, bcrypt remains acceptable. argon2id is the better choice for new systems; bcrypt is the more common choice in existing systems.

## Decision

Implement `PasswordHasher` with `BcryptPasswordHasher` using the `bcrypt` library. Work factor 12 (current default). The `needs_rehash` method inspects the hash string's work-factor prefix and returns True if the configured work factor has increased.

Current implementation lives in `backend/app/security.py`; moves to `adapters/driven/identity/bcrypt_password_hasher.py` during migration.

This adapter is the *current* choice, not the *permanent* choice. An argon2id adapter is the planned upgrade path; the `needs_rehash` mechanism enables transparent migration on next login.

## Consequences

**Easy:**
- bcrypt is mature; the implementation is short.
- Work-factor migration (12 → 13 → 14) is handled by `needs_rehash`.
- The port shape makes the argon2id upgrade an adapter swap, with same-port transition support.

**Hard:**
- bcrypt's 72-byte password length limit can bite (passphrases longer than 72 bytes truncate silently). Mitigated by pre-hashing long passwords with SHA-256 before bcrypt — but this is its own subtle concern. Document if encountered.
- Migrating to argon2id requires *both* adapters live in parallel for one transition window, or a one-shot migration script — `needs_rehash` does not bridge across algorithms unless implemented to recognize both formats. Plan the migration explicitly.

**Forecloses:**
- Direct `bcrypt` use outside the adapter.

## Alternatives considered

- **argon2id from day one** — preferred by OWASP. Reasonable to start there. bcrypt was the existing choice when this ADR was written; flipping to argon2id is on the roadmap.
- **PBKDF2** — viable; widely supported, more configurable. Less GPU-resistant than argon2id.

## Review trigger

- The argon2id transition is initiated — write a new adapter ADR superseding this one.
- A CVE or weakness emerges in bcrypt that has not appeared in a decade — unlikely but possible.
