---
id: {folder}-NNNN
title: {short imperative title — "Adopt X" / "Use Y as Z"}
status: proposed              # proposed | accepted | deprecated | superseded
date: YYYY-MM-DD
supersedes: []                # list of ADR ids this replaces, e.g. ["adapters-driven-0005"]
superseded-by: []             # filled in by a future ADR; do not set when authoring
---

## Context

What forces are in play? What problem is this decision responding to? Two or three paragraphs at most. Assume the reader has read the parent folder's README and the linked predecessor ADRs.

## Decision

One sentence. The thing we chose. If you can't say it in one sentence, the ADR is doing more than one job — split it.

## Consequences

What this makes easy. What it makes hard. What it forecloses. Be honest about the costs; an ADR with no downsides is propaganda.

## Alternatives considered

- **Option A** — rejected because {reason}.
- **Option B** — viable; would prefer if {condition}.
- **Option C** — out of scope because {reason}.

The *Alternatives considered* section is often the most valuable part of an ADR. It's where future readers learn what off-ramps exist and what would justify taking one.

## Review trigger

What specific condition would cause us to revisit this? Be concrete:

- Cost exceeds $X / month
- Latency budget exceeds Y ms at p95
- Team grows past N people
- A requirement Z arrives
- A specific named dependency is deprecated

If you cannot name a review trigger, the decision either (a) is genuinely permanent (rare) or (b) hasn't been thought through.
