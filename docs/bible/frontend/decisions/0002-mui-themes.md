---
id: frontend-0002
title: Six MUI themes (3 light, 3 dark) with localStorage persistence
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The UI offers theming. The options range from "one theme, dark mode toggle" to "fully user-customizable palette." For an app whose users spend non-trivial time reading text and visualizing graphs, theme choice matters: contrast, eye strain, and the `discrete` color palette for graph nodes.

## Decision

Ship **six MUI themes** — three light (default light, soft cream, high contrast), three dark (default dark, deep blue, charcoal). Selected theme is persisted in `localStorage`. The theme palette includes a `discrete` color array used by `GraphContent` for node/edge coloring, distinct from the default MUI palette.

Theme switching is a top-level UI control in `SettingsMenu`. No system-color-scheme auto-detection by default; the user explicitly picks. (A "match system" option may be added later as a seventh entry.)

## Consequences

**Easy:**
- Each theme is a small object; adding a seventh is a few lines.
- Graph colors are themed too — graph readability stays consistent with the rest of the UI.
- localStorage persistence is one effect hook; no state library involved.

**Hard:**
- Six themes is more visual QA than one would prefer. Each new component must be eyeballed in all six.
- The discrete color array must stay perceptually distinguishable across all themes — easy to miss when adding a new theme.

**Forecloses:**
- Per-user server-side theme persistence (settings only sync per-browser today). Acceptable; if cross-device theme sync becomes desired, store the choice on the user record via [identity](../../capabilities/identity/).

## Alternatives considered

- **One light + one dark, toggled** — viable; simpler. Six was chosen because user research / preference indicated meaningful taste variation in this audience.
- **Fully customizable palette** — rejected. The complexity (color-picker UI, palette validation, accessibility checks) is out of proportion to the benefit at this scale.

## Review trigger

- A new component is consistently hard to make readable in all six themes — indicates the palette set is too wide.
- Accessibility audits flag specific themes as failing WCAG AA — those themes get fixed or removed, not kept as "you can choose them but they're worse."
