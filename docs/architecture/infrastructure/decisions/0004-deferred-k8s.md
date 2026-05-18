---
id: infrastructure-0004
title: Kubernetes deferred until a forcing function
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Kubernetes is the dominant orchestrator at scale. It is also the most operationally complex thing the project could adopt — even a managed Kubernetes (EKS, GKE, AKS) introduces a substantial learning surface and a separate skill set to operate. The default at most companies is to adopt it; the question is whether *this* project should.

For a single-dedicated-server deployment with ~5 services, the answer is clearly no. The question is when the answer flips.

## Decision

Kubernetes is **deferred** until a concrete forcing function appears. Today the system uses [Docker Compose on a single dedicated server](./0002-docker-compose-topology.md). Compose meets every functional requirement at current scale.

Forcing functions that would justify Kubernetes:

- Multi-host scheduling becomes required (more services than one host can run, or per-host failures unacceptable).
- Auto-scaling becomes required and Compose cannot express it.
- Multi-region failover becomes a real requirement.
- An organizational pull (a parent company standardizes on K8s, a deployment partner requires it) makes it the path of least resistance.

## Consequences

**Easy:**
- Avoid a large operational complexity that would not pay off today.
- The team's focus stays on the product, not the orchestrator.

**Hard:**
- When the forcing function does arrive, adopting Kubernetes will be a multi-week effort (Helm charts, ingress, secrets management, observability stack). Plan for it; do not be surprised.
- "We don't use Kubernetes" is sometimes a hiring signal in either direction.

**Forecloses (deliberately):**
- The class of features that only K8s makes easy at the current stage.

## Alternatives considered

- **Adopt Kubernetes now** — rejected. The complexity does not match the scale.
- **Nomad** — viable as a middle-ground. Less complex than K8s, more orchestration than Compose. Reasonable alternative if Compose hits limits before K8s makes sense.

## Review trigger

- Any of the forcing functions above materializes.
- Compose-specific limitations (no rolling updates without downtime, no service mesh, no horizontal pod autoscaling) become binding for real user experience reasons.
