# Capability: Identity

Identity is the capability that turns a network request or a CLI invocation into a `Principal` — a value object carrying who is asking and what they are allowed to do.

It covers authentication (proving who you are), authorization (saying what you can do), and the lifecycle of credentials.

## Concepts

- **User** — a registered identity with credentials. Has email, username, password hash, timestamps. Also owned by [collaboration](../collaboration/) for document/workspace relationships; identity is the authoritative source.
- **Guest** — an ephemeral identity used for try-before-register flows. Has a temporary token, no persistent password, and a marker on the Principal.
- **Credentials** — what proves a user's identity. Today: email + password. Future: OAuth, passkeys, API keys.
- **Token** — an artifact a client carries to prove an authenticated session. Two kinds: a short-lived access token (15 min) and a long-lived refresh token (7 days).
- **Principal** — the in-core value object passed to every use-case. Carries user id (or guest marker), email, roles, and the source of authentication (`api_jwt` | `cli_token` | `system`).
- **Permission** — an enum of authorization capabilities (`VALIDATE_PAPER`, `MANAGE_WORKSPACE`, `ADMIN_RESET_JOBS`, etc.).
- **Role** — a named set of permissions. Mapped to permissions in a single table; not stored per-user as a permission list.

## Use-cases this capability exposes

- `RegisterUser` — create a new account.
- `Login` — authenticate with credentials, issue tokens.
- `Logout` — invalidate the refresh token.
- `RefreshSession` — exchange a refresh token for a new access token (rotates the refresh token).
- `GuestTry` — issue an ephemeral guest principal and token.
- `ChangePassword`, `RequestPasswordReset`, `ResetPassword` (planned, not yet implemented).
- `GetCurrentUser` — return the user behind the current Principal.

## Ports this capability depends on

- [`UserRepository`](../../ports/decisions/0009-repository-ports.md) — persist and query users.
- [`PasswordHasher`](../../ports/decisions/0007-password-hasher-port.md) — hash and verify passwords.
- [`TokenIssuer`](../../ports/decisions/0006-token-issuer-port.md) — mint and verify access/refresh tokens.
- [`Clock`](../../ports/decisions/0008-clock-port.md) — token expiry calculations.

## How Principal is constructed

The construction is *outside* the use-cases — it happens in the adapter that received the request:

- **HTTP API**: middleware parses the JWT from `Authorization: Bearer ...` (or the refresh token from an HTTP-only cookie), verifies via `TokenIssuer`, loads the user via `UserRepository`, builds the `Principal`, and passes it to the use-case.
- **CLI**: the entry point reads the local token (`~/.config/advisor/token` or similar), verifies via `TokenIssuer`, builds the `Principal` from token claims (no need to call `UserRepository` for each invocation), passes it to the use-case.
- **System / internal jobs**: the orchestrator that triggers the job constructs a `Principal(role="system")` directly. This is the only path that does not pass through a real credential — it is reserved for internal use and audited as such.

## What this capability is *not*

- Not a session store. Token validity is checked cryptographically (JWT signature + expiry), not by lookup. The refresh token is the only stateful artifact.
- Not a full identity provider. It does not support enterprise SSO, SAML, or org-level identity federation today. Those become future ADRs if/when the requirement arrives.
- Not the authorization policy engine. It defines `Principal` and `Permission`; the *use* of permissions to allow/deny actions lives inside each use-case via `authz.require(principal, Permission.X)`.

## ADRs in this capability

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-jwt-with-refresh-rotation.md) | JWT access + refresh token rotation | accepted |
| [0002](./decisions/0002-guest-try-flow.md) | Guest try flow (ephemeral identity) | accepted |
| [0003](./decisions/0003-role-based-not-policy-engine.md) | Role-based authz; no policy engine yet | accepted |
