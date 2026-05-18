---
id: process-0002
title: ADR authoring and lifecycle
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

[0001 — Use MADR format for ADRs](../../decisions/0001-use-madr-format.md) chose MADR as the format. It does not specify the *workflow* — how new ADRs are proposed, reviewed, accepted, superseded, or rejected. Workflow gaps lead to inconsistent practice: some ADRs land as `accepted` without review; some sit as `proposed` indefinitely; some are edited in place when they should be superseded.

## Decision

The ADR lifecycle is:

### Proposing

1. Copy [adr-template.md](../../adr-template.md) into the appropriate `decisions/` folder.
2. Number it: next available `NNNN-` in that folder.
3. Set `status: proposed`.
4. Fill in *Context*, *Decision*, *Consequences*, *Alternatives considered*, *Review trigger*.
5. Open a PR.

### Reviewing

- Discussion happens *in the PR*, not in chat or other channels. The PR's history is the ADR's argument trail.
- The PR may amend the ADR's content (Context, Alternatives) freely as discussion develops. The *Decision* sentence may change — that is the point of discussion.
- A reviewer's "I'd prefer Y" is a comment; the ADR's author resolves it by either changing the Decision or recording Y in *Alternatives considered* with the rationale for rejection.

### Accepting

- An ADR is accepted by merging the PR with `status: accepted`.
- The PR must have approval from at least one team member other than the author. For cross-cutting ADRs (anything under `architecture/`), two approvals.

### Rejecting

Two options:

1. **Merge as `proposed` with a rejection note** in the body explaining why and what was decided instead. Preserves the reasoning trail for future readers.
2. **Close the PR without merging.** Faster; the reasoning is lost to PR history.

Option 1 is preferred for cross-cutting or contentious decisions; option 2 is acceptable for small adapter or implementation ADRs that did not survive review.

### Superseding

Never edit an `accepted` ADR's *Decision*. To change the decision:

1. Write a new ADR with the new decision.
2. New ADR's frontmatter: `supersedes: ["<predecessor-id>"]`.
3. Predecessor ADR's frontmatter: `status: superseded`, `superseded-by: ["<new-id>"]`.
4. Both changes land in the same PR.

Editing an accepted ADR's *Context*, *Consequences*, or *Alternatives* sections for clarity (typos, link fixes) is allowed and does not require supersession. Editing the *Decision* is not.

### Deprecating

`status: deprecated` means "we no longer recommend this, but it is still present in code." This is used when the replacement is not yet implemented but the direction is clear. An ADR can be `deprecated` without a `superseded-by` link.

## Consequences

**Easy:**
- A new contributor opens a PR; the workflow is the same as any other.
- The history of why-we-decided-this is preserved by the supersession chain, not by archeology.
- Reviewers can be opinionated without blocking — the *Alternatives considered* section absorbs opinions.

**Hard:**
- Writing an ADR is small but real overhead. The first time someone proposes a structural change and is asked to write an ADR, there is friction. The friction is the point: it forces "is this decision worth recording?" to be answered consciously.
- Supersession discipline requires not editing in place. Tempting, especially for minor decision drift.

**Forecloses:**
- Edit-in-place decision drift.
- "We decided this in a meeting" without a written artifact.

## Alternatives considered

- **No formal lifecycle; ADRs are just docs** — rejected. Decays into "some docs are accurate, some are not, who knows."
- **All ADRs require team-wide consensus** — rejected. Too high a bar; small adapter decisions would never land.

## Review trigger

- The workflow generates more friction than value — e.g., trivial decisions are blocked waiting for ADRs.
- ADRs are routinely edited in place despite this rule. At that point the rule is wrong or the team is wrong; identify which.
