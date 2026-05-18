---
id: architecture-0004
title: Ports are `typing.Protocol`, not abstract base classes
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Ports are the interfaces the core declares for infrastructure. Python offers two ways to express an interface: `abc.ABC` with `@abstractmethod` (nominal typing — adapters must inherit and import the ABC) and `typing.Protocol` (structural typing — adapters only need matching method signatures).

The choice affects the *direction* of the dependency between core and adapters and shapes how easily fakes can be written for tests.

## Decision

Ports are declared as `typing.Protocol` classes (annotated with `@runtime_checkable` when an isinstance check is needed; otherwise plain `Protocol`). Adapters satisfy ports structurally; they are not required to inherit from or import the port definition.

## Consequences

**Easy:**
- The dependency direction is strictly one-way: `core/ports/` depends on nothing in `adapters/`, and `adapters/driven/*` need not import `core/ports/` to satisfy a port.
- Test fakes are trivial: any object with the right method signatures is a valid implementation. No mock library required.
- A real adapter and a test fake are the same kind of object from the core's perspective.

**Hard:**
- Structural typing is silent: a method-name typo in an adapter is not caught at import time. It surfaces as an `AttributeError` at first call, or — worse — as a type-checker warning that an inattentive contributor may ignore. Mitigation: type-check the adapter against the port explicitly in tests (`def _check(s: JobStore = SqliteJobStore()): pass`).
- IDE refactor tools (rename method across implementers) work less reliably with structural typing than with nominal inheritance.

**Forecloses:**
- Default-method implementations on the port itself (Protocols can have defaults, but using them blurs the port/adapter line). Keep ports as pure signatures.
- ABCs anywhere in the port layer.

## Alternatives considered

- **`abc.ABC` with `@abstractmethod`** — rejected. Forces adapters to import from `core/ports/`, which reverses the dependency direction the architecture is built to enforce.
- **`typing.Protocol` *with* `@runtime_checkable` everywhere** — rejected as default. `@runtime_checkable` is slower at `isinstance` time and rarely needed; use only where runtime checks are required.
- **No interface at all; rely on duck typing** — rejected. The Protocol *is* the contract. Without it, the use-case cannot be type-checked against its dependencies, and a new contributor has no way to know what an adapter must implement.

## Review trigger

- The team finds itself repeatedly forgetting required methods because Protocol typos are silent. At that point either (a) enforce per-adapter assignment tests in CI, or (b) reconsider ABCs.
- A future Python version makes Protocol method enforcement strict at class-creation time — at which point the trade-off shifts.
