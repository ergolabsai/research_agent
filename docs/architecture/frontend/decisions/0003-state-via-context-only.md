---
id: frontend-0003
title: React Context for state; no external state library
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The frontend has several pieces of cross-component state: authentication (current user, tokens), theme, dialog stacks, and per-page data. The React ecosystem offers several state-management approaches:

- **React Context + `useState`** — built-in, no dependency. Re-renders propagate through provider subtrees.
- **Redux** — long-standing, ceremony-heavy, mature DevTools.
- **Zustand** — lightweight global store with hooks. Currently installed but unused.
- **Jotai / Recoil** — atomic state.
- **React Query / TanStack Query** — server-state caching; not a general state library.

`zustand` is listed in `package.json` but no component imports it — a leftover from earlier exploration.

## Decision

Use **React Context + `useState`** for cross-component state. No external state-management library. Server-state caching is handled per-call by hooks (with axios) rather than a generic cache layer.

The state surfaces today: `AuthProvider`, `ThemeProvider`, dialog context. Each is small enough that Context's re-render behavior is not a problem.

`zustand` should be removed from `package.json` on the next dep cleanup pass.

## Consequences

**Easy:**
- One mental model: providers and hooks. No external API.
- No bundle bloat from a state library.
- Adding a new context is one provider + one hook.

**Hard:**
- Context re-render behavior can surprise — every consumer re-renders when the value object changes, even if the part they consume did not change. Mitigated by splitting contexts narrowly (auth, theme, dialogs are separate) and memoizing values.
- No DevTools for state inspection beyond React DevTools' Context panel.

**Forecloses:**
- Time-travel debugging.
- Persisted state across tabs without manual `BroadcastChannel` plumbing (acceptable; not a current need).

## Alternatives considered

- **Redux Toolkit** — viable; mature. Rejected as overkill for the current state surface (auth + theme + dialogs is not a state-management problem).
- **Zustand** — viable; less ceremony than Redux. Removed from this project because no component uses it; if a future need appears, adding it back is cheap.
- **React Query / TanStack Query** — viable specifically for server state. Worth revisiting if API call patterns become repetitive (the same endpoints fetched from multiple components without coordination).

## Review trigger

- A piece of state becomes painful to model with Context — typically when many components need it *and* it changes often *and* the re-render cost is real.
- API call patterns develop enough duplication that a server-state cache layer (React Query) becomes worth its dependency.
