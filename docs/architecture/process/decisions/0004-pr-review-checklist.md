---
id: process-0004
title: PR review checklist for layered code
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The architecture relies on disciplined code review. Without a structured checklist, reviewers default to "looks fine" for changes that touch the boundaries — especially when the change is small or the reviewer is rushed. The classes of issue that the architecture cares about (I/O in core, adapters with business logic, missing Principal, ABC instead of Protocol) are not caught by general "looks fine" review.

A checklist makes the architecture's expectations visible and applies the same prompts on every PR.

## Decision

The PR template (in `.github/PULL_REQUEST_TEMPLATE.md` or equivalent) carries a checklist that must be ticked for any PR touching `core/`, `adapters/`, or `composition/`:

- [ ] **No I/O imports in `core/`.** If a new dependency was added under core, it appears in the allow-list and is justified.
- [ ] **Adapters are dumb.** Driving adapters: parse → call use-case → format. Driven adapters: implement port → translate to/from infrastructure. No business logic.
- [ ] **`Principal` is the first argument of every new use-case.** Authorization is checked inside the use-case via `authz.require(...)`.
- [ ] **New ports are `typing.Protocol`,** not ABC.
- [ ] **Driving adapters do not import driven adapters.** Going through composition is the path.
- [ ] **If a new use-case has a CLI command, it also has an API route** (or there is a tracked issue to add it). The CLI is first-class per [0007 — CLI-first driving adapter](../../decisions/0007-cli-first-driving-adapter.md).
- [ ] **The change passes the "could an AI agent rebuild this in isolation?" check** ([process/0003](./0003-ai-agent-rebuild-test.md)) for any `core/` file modified.
- [ ] **`import-linter` is green.**

For PRs touching only frontend, infrastructure, or docs: the checklist is irrelevant; reviewers use general judgment.

## Consequences

**Easy:**
- A reviewer knows what to look for without remembering the architecture rules.
- The checklist anchors the conversation when something is missed — "this isn't ticked; let's discuss."
- New contributors learn the rules by encountering the checklist on their first PR.

**Hard:**
- Checklists can become rubber-stamped. Mitigated by reviewers asking "where in the code is item N satisfied?" when in doubt.
- Items will need updating as the architecture evolves. Treat the checklist as living; ADRs that change boundary rules also update the checklist.

**Forecloses:**
- Reviewers approving boundary-breaking changes silently.

## Alternatives considered

- **No checklist; rely on reviewer judgment** — rejected. The architecture is too recent in the team's habits; the checklist is the scaffolding while habits form.
- **Long-form checklist** — rejected. Reviewers ignore long lists. Eight items max; trim as automation absorbs items.

## Review trigger

- An item on the checklist is automated (e.g., a CI script that verifies "use-cases take Principal first"). Drop the item from the checklist — automation is stronger.
- An item is consistently ignored or rubber-stamped. Either the item is wrong (revise) or the team is wrong (training).
- The list grows past eight items. Something gets dropped or merged.
