---
id: infrastructure-0003
title: nginx for TLS termination, static serving, and routing
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The application stack needs a public-facing endpoint that:

- Terminates TLS (certificates from Let's Encrypt or a managed provider).
- Routes `/api/*` to the FastAPI container.
- Serves the built frontend (`dist/`) for everything else.
- Serves `/static/attachments/*` from the local-filesystem object-storage adapter (during pre-alpha; replaced by signed URLs in production with MinIO).

Standard answers: nginx, Caddy, Traefik. All work. Differences are operational style.

## Decision

Use **nginx**. Configuration lives under `deploy/nginx/` with a `nginx.conf` and per-upstream snippets in `conf.d/`. Run as one of the Compose services.

TLS certificates are obtained via certbot (or the equivalent for the chosen DNS provider) and mounted into the nginx container. Renewal is a cron-driven script.

## Consequences

**Easy:**
- nginx is extremely well-understood; operational knowledge is widely available.
- The configuration is plain text, version-controlled, diffable.
- Adding a new upstream (e.g., a pipeline-service container post Step 5 of migration) is a few lines.

**Hard:**
- Manual certbot management has its own failure modes (cron job stops working; certs expire). Use a known-good script and an external monitor.
- nginx config syntax is its own thing — easy to make small mistakes that produce surprising routing behavior.

**Forecloses:**
- Auto-TLS via the proxy itself (Caddy does this transparently). nginx requires certbot or an equivalent companion.

## Alternatives considered

- **Caddy** — viable; auto-TLS is genuinely simpler. Rejected because nginx is more battle-tested and the team has more nginx experience. Caddy is the right answer for a project that prizes operational simplicity over familiarity.
- **Traefik** — viable; integrates with Docker labels for auto-routing. Adds magic; less explicit configuration.

## Review trigger

- Multiple environments diverge in routing rules enough that nginx config becomes a maintenance burden. At that point either factor into includes more aggressively or evaluate Caddy/Traefik.
- A genuine need for per-request rules (rate limiting per user, A/B routing) appears that nginx handles awkwardly.
