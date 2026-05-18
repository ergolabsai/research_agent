---
id: frontend-0001
title: Vite + SPA shape
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The frontend can be structured as:

- **Single-page application (SPA)** — JS bundle owns routing; first paint waits for JS; deep links re-enter the SPA via fallback.
- **Server-rendered (SSR)** — HTML rendered at request time; faster first paint; runtime server overhead.
- **Static site (SSG)** — pre-rendered at build time; fastest first paint; no per-user content rendered on server.

The validation UI is *highly* interactive: live polling of a job, graph view with force-directed rendering, math and markdown rendering, theming, auth-gated everything. SSR/SSG would add complexity (a Node runtime in production, hydration boundaries) for marginal benefit when most of the UI is auth-gated and dynamic anyway.

Vite is the dev/build tool. Alternatives: webpack (older, slower), Parcel (smaller community).

## Decision

The frontend is a **single-page application** built and served by **Vite**.

- Dev: `vite` on port 4174 with HMR and `/api` proxied to the FastAPI backend.
- Prod: `vite build` produces a static `dist/` served by nginx.

A mock-mode (`npm run dev:mock`) intercepts axios calls with fixtures from `src/mocks/` for frontend-only iteration.

## Consequences

**Easy:**
- Fast dev experience (HMR, sub-second reload).
- Static-asset production deployment: drop `dist/` behind nginx, done.
- Mock mode lets frontend developers iterate without the backend.

**Hard:**
- First paint waits for the JS bundle. Acceptable because the UI is mostly auth-gated; users do not arrive on a landing page they need to see in under a second.
- Code splitting must be applied deliberately; the default is one big bundle.

**Forecloses:**
- Server-side rendering as a default. If a future need appears (e.g., SEO for a public landing page), a small SSR shell at the edge is possible without changing the SPA.

## Alternatives considered

- **Next.js (SSR/SSG)** — viable; the conventional React-with-SSR choice. Rejected for the dynamic-content reason above plus the operational cost of a Node runtime in production.
- **Remix** — viable; similar to Next. Same rejection reasons.
- **Webpack + custom config** — rejected. Older, slower, more configuration burden.

## Review trigger

- SEO becomes a real product requirement (public landing pages with shared papers).
- First-paint latency becomes a binding UX problem and code-splitting alone is insufficient.
