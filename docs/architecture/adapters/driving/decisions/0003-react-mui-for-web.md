---
id: adapters-driving-0003
title: React + MUI + Vite as the web driving adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The web frontend is a driving adapter on top of the HTTP API. It is the most user-facing surface and the one where the system's perceived quality is most strongly shaped. Constraints: SPA-style routing (no full-page reloads), JWT-based session management, math rendering (KaTeX) and figure display, theming, markdown rendering.

The project is already on React 18 + MUI v5 + Vite. This ADR records the choice as a deliberate one rather than as inertia, and lists the specific framework decisions that go with it.

## Decision

The web frontend is:

- **React 18** for the component model.
- **MUI v5** (Material UI) for component library and theming. Six built-in themes (3 light, 3 dark) persisted in localStorage.
- **Vite** for build + dev server. Proxies `/api` to the FastAPI backend.
- **TypeScript** throughout. Strict mode.
- **React Router v6** for client-side routing.
- **Axios** as the HTTP client, with interceptors for JWT refresh.
- **`react-markdown` + `remark-gfm`** for markdown rendering.
- **`react-force-graph-2d`** for the paper-graph visualization.
- **KaTeX** for math rendering.

Types consumed by the frontend (`ValidationResult`, `GraphAnalysis`, etc.) are *generated* from the backend's Pydantic contracts (see [frontend/0004](../../../frontend/decisions/0004-generated-types-from-contracts.md)).

## Consequences

**Easy:**
- A large ecosystem of MUI components and React patterns is available; productivity is high.
- Vite's dev experience (HMR, fast startup) is good.
- TypeScript + generated types from contracts mean the frontend cannot drift silently from the backend.

**Hard:**
- React + MUI is a heavy initial-load surface. Code-splitting and bundle analysis are recurring concerns, not one-time.
- MUI's customization API is layered (`sx` props, theme overrides, styled API); inconsistent use leads to drift.
- Dead-dependency creep is real — the codebase already accumulated `draft-js`, `react-draft-wysiwyg`, `zustand` without using them. Regular pruning passes are needed.

**Forecloses:**
- Switching to a different component library without a substantial rewrite.

## Alternatives considered

- **Other React component libraries** (Chakra, Mantine, Ant Design) — viable; MUI's choice is established and the cost of switching is not justified by a marginal API preference.
- **A different framework** (Vue, Svelte, Solid) — rejected for project continuity. The team has React expertise.
- **No SPA; server-rendered HTML** — rejected. The validation UI is interactive enough (graph view, live polling, math/markdown rendering) that a SPA is the right shape.

## Review trigger

- MUI v5 hits end-of-life or v6+ introduces breaking changes the project cannot accept.
- Bundle size becomes a binding user-experience problem (perceived load time crosses a tolerance threshold) and code-splitting alone is insufficient.
- A native desktop or mobile app is built; at that point the web frontend's architectural choices stay but the cross-platform shape gets reconsidered.
