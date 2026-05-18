---
id: ports-0008
title: `Clock` port for injectable time
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Code that reads the current time from a global (`datetime.now()`, `time.time()`) is hard to test deterministically. Tests that depend on time either freeze the clock with monkey-patching libraries (`freezegun`) or accept flakiness around time-sensitive logic (token expiry, job timeouts, scheduled tasks).

A port for time costs little (one method, one implementation) and pays back every time a test needs to control time.

## Decision

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

Returns a timezone-aware `datetime` in the project's standard timezone (`America/Los_Angeles`). Every use-case and service that needs "now" takes `Clock` in its constructor. No direct `datetime.now()` calls in core.

## Consequences

**Easy:**
- Tests pass a `FrozenClock(at=datetime(2026, 1, 1, ...))` or a `TickingClock` that advances on each call. Time-sensitive tests become deterministic.
- The project's timezone convention is encoded once, in the adapter.

**Hard:**
- The port is *not async*. This is a deliberate exception: time access is trivially fast and adding `await` everywhere would be noise. The port stays sync.

**Forecloses:**
- Direct `datetime.now()` or `time.time()` in core. `import-linter` enforces this if configured to.

## Adapters

- **`SystemClock`** — current default. Returns `datetime.now(tz=APP_TIMEZONE)`.
- **`FrozenClock`** — test fake. Returns a fixed time.
- **`TickingClock`** — test fake. Advances by a configurable delta on each `now()` call.

See [adapters/driven/decisions/0012-system-clock.md](../../adapters/driven/decisions/0012-system-clock.md).

## Review trigger

- Distributed-system needs introduce a "logical clock" (Lamport, vector). At that point a *separate* port (`LogicalClock`) is added; the wall-clock port stays.
