---
id: architecture-0011
title: Single repo, defer splitting
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A hexagonal architecture is sometimes used as the on-ramp to a multi-repo split: core in one repo, each adapter in its own. The split has real benefits — independent release cadences, scoped review surfaces, separate CI — but also real costs: cross-repo PRs, version coordination, contracts published as packages, more moving parts at deploy time.

For a 3–5 person team that has not yet shipped production, the cost is higher than the benefit. But the option must remain available, because the moment a team or deployment-pipeline boundary appears, the cost flips.

## Decision

The project stays in a **single repo** for now, with the hexagonal layout internalized. Splitting is **deferred** — not forbidden — until a concrete forcing function appears.

Forcing functions that would justify splitting:

- A separate team takes ownership of a layer (e.g., a "pipeline" team and an "app" team with different review cadences).
- The pipeline must be released independently of the API on a recurring basis, and version skew between them becomes hard to manage in one repo.
- `core/` becomes a public contracts package consumed by external integrators (e.g., a published SDK for partners building connectors).
- The CI matrix becomes unwieldy because changes to one adapter trigger full rebuilds across the rest.

## Consequences

**Easy:**
- One review process, one CI pipeline, one issue tracker.
- Atomic refactors across layers are normal commits, not coordinated PR campaigns.
- Onboarding is a single clone-and-install.

**Hard:**
- Boundaries are enforced only by lint and review. A determined contributor (or a careless agent) can violate them more easily than across repo boundaries.
- The temptation to add cross-layer "shortcuts" is constant; mitigated by [0006](./0006-no-short-circuit-imports.md) and CI.

**Forecloses (for now):**
- Independent release versioning per layer. Today every commit ships the whole repo.
- Locked-down access controls per layer (e.g., contractors who only see the frontend repo).

## Cheap-split property

The hexagonal layout makes the future split cheap when a forcing function does arrive:

- `core/` becomes its own repo (`research-advisor-core`), published to a private index.
- Each adapter becomes its own repo; depends on `research-advisor-core` as a pinned version.
- `composition/` lives in whichever deployable owns the entrypoint (the API repo, the CLI repo, etc.).
- Contracts are already isolated, so the published-package interface is already drawn.

The point of staying single-repo *now* is to capture this option later without paying for it today.

## Alternatives considered

- **Three repos up-front (`core`, `backend`, `pipeline`)** — rejected. This was an earlier draft of the architecture plan. The benefits do not yet justify the operational overhead; the hexagonal layout gives most of the isolation benefit inside one repo.
- **Monorepo with build-tool isolation (Bazel, Nx, Pants)** — rejected. Out of proportion to team size.
- **Polyrepo from the start with contracts as a published package** — viable; reconsidered if the SDK forcing function arrives first. Until then, premature.

## Review trigger

- Any of the four forcing functions above materializes.
- Cross-layer refactors stop being atomic because layers are owned by different reviewers who block each other.
