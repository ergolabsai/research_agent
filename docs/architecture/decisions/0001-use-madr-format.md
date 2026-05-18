---
id: architecture-0001
title: Use MADR format for ADRs
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The project's architectural choices were previously embedded in prose across `docs/ARCHITECTURE.md` and `docs/architecture/*.md`. Finding "is X locked or in flux?" required reading paragraphs and inferring tone. As the team grows and AI coding agents become routine collaborators, this is unsustainable: every reader (human or otherwise) re-derives context from prose and drifts.

A bootstrapping format must be chosen before any other decision is recorded.

## Decision

Use a lightweight variant of the **MADR** (Markdown Architecture Decision Records) format with two custom additions: `supersedes` / `superseded-by` frontmatter fields and a `Review trigger` section.

## Consequences

**Easy:**
- Status is visible at a glance via frontmatter.
- Decision *history* is preserved by the supersession chain — old reasoning is not lost when an approach changes.
- `Review trigger` forces decisions to be falsifiable rather than aspirational.
- The format is recognized by tooling (e.g., `adr-tools`, ADR viewers) without modification.

**Hard:**
- Requires discipline to write a new ADR rather than edit an old one.
- The "two extra fields" are non-standard; tools that strictly enforce MADR will warn. Acceptable trade-off.

**Forecloses:**
- More elaborate ADR systems (Y-Statements, full RFC-style documents) — those would impose ceremony out of proportion to current team size.

## Alternatives considered

- **No format; prose in `ARCHITECTURE.md`** — rejected. This is the current state and the reason this decision exists.
- **Y-Statements** (one-sentence ADRs) — rejected. Too terse to capture *Alternatives considered*, which is often the most valuable part.
- **Full RFC documents** — rejected. Ceremony out of proportion to a 3–5 person team.
- **Confluence / Notion / wiki** — rejected. Decisions belong next to the code they constrain, in the same repo, in the same review process.

## Review trigger

- Team grows past ~15 people and lightweight ADRs no longer carry enough context.
- The supersession chain becomes hard to follow because too many ADRs exist (>200) — at that point, tooling beyond Markdown becomes attractive.
