---
id: infrastructure-0002
title: Docker Compose as the deployment topology
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The dedicated server ([0001](./0001-single-dedicated-server.md)) runs several processes: the API, the frontend (static), nginx, the MCP calculator server, optionally Postgres/Redis/MinIO. They must be started, restarted, networked, and updated as a unit.

Two operational shapes:

- **systemd units** — bare-metal, one unit per service, networking via localhost ports. Lightweight but every service is a hand-rolled unit file.
- **Docker Compose** — one declarative file, each service in a container, shared network, easy version pinning.

For a team that already containerizes for dev (`make dev`), Compose is the natural production topology — same images, same network shape, same env vars.

## Decision

Production runs **Docker Compose** with separate Dockerfiles per service:

```
deploy/docker/
├── base.Dockerfile           # shared base image with Python deps
├── api.Dockerfile            # builds composition/api_app.py
├── pipeline.Dockerfile       # worker image (post Step 5 of migration)
├── cli.Dockerfile            # useful for CI; rarely deployed
├── frontend.Dockerfile       # nginx serving the Vite build
└── mcp-calculator.Dockerfile # MCP server sidecar
```

```
deploy/compose/
├── docker-compose.yml        # base: api + frontend + postgres + redis + minio + mcp
├── docker-compose.dev.yml    # override: hot-reload, exposed ports, dev env
└── docker-compose.gpu.yml    # GPU overlay (when LLM inference goes local)
```

systemd may be used at the *outer* layer to start `docker compose up` on boot — but the service definitions live in Compose, not in systemd unit files.

## Consequences

**Easy:**
- Service definitions are version-controlled, declarative, and identical across environments (override files for per-env differences).
- Updating a service is `docker compose pull <service> && docker compose up -d <service>`.
- Image pinning via tags means deploys are reproducible.

**Hard:**
- Docker introduces a dependency and a security surface (the daemon). Acceptable.
- Compose's networking model is simpler than Kubernetes' but learning it still has a curve.
- Per-service image builds are slower than a single mega-image; mitigated by a `base.Dockerfile` shared by all Python services.

**Forecloses:**
- A "just SSH and `git pull`" workflow on the production box. Deploys go through image builds.

## Alternatives considered

- **systemd units** — viable; lower overhead. Rejected because Compose's declarative service definitions are clearer and align with dev.
- **Podman + Quadlet** — viable; a Compose alternative. Same shape with different tooling. Reasonable upgrade path if Docker becomes a problem.
- **Nomad** — overkill for this scale.

## Review trigger

- The service count grows past what one Compose file pleasantly manages (~10 services).
- A genuine need for cluster-level orchestration appears (multi-host scheduling, auto-scaling). At that point Kubernetes or Nomad becomes warranted ([0004](./0004-deferred-k8s.md)).
- Compose-specific limitations (no rolling updates without downtime, no service mesh) become binding.
