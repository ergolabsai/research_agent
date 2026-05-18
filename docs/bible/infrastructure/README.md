# Infrastructure

How the system *runs*. Outside the hexagon — the core, ports, and adapters are unaware of what is in this folder.

Infrastructure decisions cover: where the system is deployed, what containerizes it, what fronts it, how secrets and config flow at deploy time, what observability is wired up. They are explicitly *not* about which library or which Python package — those are adapter concerns.

## ADRs in this folder

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-single-dedicated-server.md) | Single dedicated server (with managed services) | accepted |
| [0002](./decisions/0002-docker-compose-topology.md) | Docker Compose as the deployment topology | accepted |
| [0003](./decisions/0003-nginx-tls-termination.md) | nginx for TLS termination and routing | accepted |
| [0004](./decisions/0004-deferred-k8s.md) | Kubernetes deferred until forcing function | accepted |

## Conventions

- **`deploy/` directory** is the root of all infrastructure assets — Dockerfiles, compose files, nginx config, systemd units, migration scripts. The same `composition/api_app.py` deploys to local dev, the dedicated server, or (someday) Kubernetes with only environment changes.
- **Secrets never live in the repo.** `.env.example` is checked in (documented template); `.env.dev` and `.env.prod` are gitignored. Production secrets are materialized from a secrets manager at deploy time.
- **CI lives in `.github/workflows/`**, not under `deploy/`. CI builds and ships infrastructure; it is not infrastructure itself.
