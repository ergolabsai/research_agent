---
id: infrastructure-0001
title: Single dedicated server with managed support services
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The project is moving from a prototype that runs on developer laptops to a deployment that real users (initially a small group, growing) can reach. Three deployment shapes are common at this stage:

1. **PaaS** (Heroku, Render, Fly.io) — fastest to ship, opinionated, scales to a point, locks in some choices.
2. **Single dedicated server with managed support services** — one rented box, plus managed Postgres/Redis/object storage from services that specialize in them.
3. **Kubernetes** — flexible, complex, expensive in time even if cheap in dollars.

For a 3–5 person team with a few hundred users in sight and a thoughtful preference for predictable cost, option 2 is the right shape. The dedicated server runs the application and MCP servers; Postgres, Redis (if/when introduced), and S3-compatible object storage are managed externally.

## Decision

Deploy to a **single dedicated server** (e.g., Hetzner, OVH, dedicated provider of choice) running the FastAPI application, the React frontend (served statically by nginx), and the MCP servers. Supporting infrastructure (Postgres, Redis, MinIO/S3) is either managed externally or runs in containers on the same box, depending on cost and operational appetite.

The system is *not* deployed across multiple machines today. Horizontal scaling is deferred until the single-box ceiling is approached.

## Consequences

**Easy:**
- One machine to monitor, log, secure, and back up. Operations stay simple.
- Predictable cost — dedicated servers have flat monthly pricing without per-request surprises.
- Latency between application and MCP servers is local (same box), avoiding the egress cost and complexity of remote MCP transport.

**Hard:**
- Single point of failure. If the box dies, the system is down until restored from backup or migrated to a replacement.
- Vertical scaling has a ceiling. When the box can no longer keep up, horizontal scaling becomes urgent rather than gradual.
- Manual operational tasks (OS updates, security patches) on the box must be done; not Someone Else's Problem the way a PaaS is.

**Forecloses:**
- Multi-region deployment without significant rearchitecture.
- True high availability without secondary infrastructure.

## Alternatives considered

- **PaaS** — viable; trades flexibility for time-to-deploy. Acceptable if cost and lock-in are not concerns; the project chose self-managed for cost predictability and to keep MCP servers local.
- **Cloud VMs (EC2, GCE)** — viable; cost is higher than dedicated for equivalent compute, and the managed-services pull is real (the path of least resistance becomes "use RDS, use ElastiCache, use S3" and the bill grows).
- **Kubernetes from day one** — rejected ([0004](./0004-deferred-k8s.md)).

## Review trigger

- The single-box ceiling becomes a binding latency or capacity issue.
- Availability requirements demand multi-region failover.
- Cost trade-offs shift (e.g., a PaaS or cloud offer becomes meaningfully better).
