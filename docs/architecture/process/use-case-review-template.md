# Use-Case Review Template

A structured template for reviewing and reporting on the implementation of a use-case. Fill in each section; leave a section blank only if it genuinely does not apply, with a one-line note explaining why.

---

## Overview

**Use-case:** `{ClassName}` — one-sentence description of what it does for the user.  
**Location:** `core/use_cases/{capability}/{file}.py`  
**Capability:** identity / validation / collaboration / knowledge  
**Reviewer:**  
**Date:**  
**Commit:**

---

## Architecture Checklist

Derived from [process/0004 — PR review checklist](./decisions/0004-pr-review-checklist.md). Tick each item or note the exception.

- [ ] **No I/O in `core/`.** The use-case imports only from `core/contracts/`, `core/ports/`, and the standard library.
- [ ] **Ports used, not implementations.** The use-case constructor takes `Protocol` types, not concrete adapter classes.
- [ ] **`Principal` is present.** The use-case accepts a `Principal | None` as a parameter (or documents why it is omitted — e.g., pre-auth flows like login/register).
- [ ] **Driven adapters are dumb.** Any new adapter method translates data and delegates to infrastructure; no business logic lives in it.
- [ ] **Composition wires it.** A `get_{use_case}()` factory exists in `composition/container.py` and is the only place the use-case is constructed.
- [ ] **Route is thin.** The driving adapter does: parse request → call use-case → map domain error to HTTP status → return. No logic beyond that.
- [ ] **New ports are `typing.Protocol`.** No ABCs introduced.
- [ ] **`import-linter` is green.**

---

## Security Checklist

Tick each item or mark N/A with a note.

- [ ] **No credential enumeration.** A single error type is raised for both "not found" and "wrong credential" cases, preventing callers from distinguishing them.
- [ ] **Input validated at the boundary.** Pydantic `Field` constraints on the driving adapter's request model; the use-case trusts its inputs.
- [ ] **Sensitive data not leaked in errors.** `DomainError` messages contain no PII, raw hashes, or internal identifiers.
- [ ] **Token claims are minimal.** Access tokens carry only what downstream code needs (sub, email, roles, is_guest, iat, exp).
- [ ] **Password hashing is adapter-owned.** The use-case calls `PasswordHasher.hash()` / `.verify()` — it never sees a raw bcrypt call.
- [ ] **Rehash path is safe.** If `needs_rehash` is checked, the new hash is persisted before tokens are issued.
- [ ] **No secrets in logs or tracebacks.** Exceptions raised by the use-case do not embed passwords, tokens, or raw hashes.

---

## Functional Correctness

Evaluate whether the use-case does what it claims, and whether its presence is safe for the rest of the codebase.

### Behaviour verification

- [ ] **Happy path is correct.** The use-case produces the right output for a valid, well-formed request.
- [ ] **Failure paths are correct.** Every documented `raise` is reachable and produces the right error type and message.
- [ ] **Edge cases are handled.** Boundary inputs (empty strings, maximum lengths, null optional fields, concurrent duplicate submissions) behave as expected.
- [ ] **Side effects are intentional.** Every write to a port (repository, token issuer, hasher) is necessary and ordered correctly. No silent no-ops.
- [ ] **Response shape matches the contract.** The response dataclass fields align with what callers (routes, tests, frontend types) expect — no field added or removed without a corresponding update downstream.

### Codebase-wide impact

_For each item below, note the files or call-sites examined and confirm no regression was introduced._

| Area                                                     | Files / call-sites checked | Verdict |
| -------------------------------------------------------- | -------------------------- | ------- |
| Other use-cases in the same capability                   |                            |         |
| Driving adapter routes that call this use-case           |                            |         |
| Driven adapter methods added or modified                 |                            |         |
| Contracts or port methods added or modified              |                            |         |
| Composition container changes                            |                            |         |
| Frontend types or API client affected                    |                            |         |
| Other capabilities that share the same ports or adapters |                            |         |

### Invariants upheld

_List any system-wide invariants this use-case must preserve (e.g., "every created user has a unique email across both email and username columns", "a guest account is never issued a non-guest role"). Confirm each is still true after this change._

- ***

## Implementation Findings

### What is good

_List things done well — correct security posture, clean boundary adherence, good naming, useful docstring, injected TTL for testability, etc. Record from success as well as failure._

-

### Issues

Group by severity. Remove a severity band if it has no entries.

#### Critical / High Risk

_Bugs or security issues that must be fixed before the use-case ships._

|     | File | Finding | Recommended fix |
| --- | ---- | ------- | --------------- |
| 1   |      |         |                 |

#### Medium Risk

_Design issues, performance problems, or missing invariants that should be addressed soon._

|     | File | Finding | Recommended fix |
| --- | ---- | ------- | --------------- |
| 1   |      |         |                 |

#### Low Risk

_Minor improvements, style, missing comments on subtle invariants, dead imports._

|     | File | Finding | Recommended fix |
| --- | ---- | ------- | --------------- |
| 1   |      |         |                 |

---

## Test Coverage

- [ ] Unit tests exist for the happy path.
- [ ] Unit tests cover the primary failure paths (e.g., `InvalidCredentials`, `DuplicateEmail`).
- [ ] The enumeration-safety contract is tested explicitly (if applicable).
- [ ] Edge cases are covered (e.g., guest upgrade path, rehash path, empty identifier).

**Notes:** _Location of test file(s), or explanation if tests are deferred._

---

## What's Next

_The logical next use-case or follow-up task, with a one-line rationale._
