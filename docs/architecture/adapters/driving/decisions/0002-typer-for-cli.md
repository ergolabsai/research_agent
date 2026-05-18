---
id: adapters-driving-0002
title: Typer as the CLI driving adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The CLI is the first-class driving adapter ([0007 — CLI-first driving adapter](../../../decisions/0007-cli-first-driving-adapter.md)) and must be agent-friendly: `--json` output on every command, predictable exit codes, fast startup.

Two Python CLI frameworks are dominant: **Click** (mature, decorator-based, well-tested) and **Typer** (built on Click, type-hint-driven, more concise). Both meet the functional requirements; the difference is ergonomics.

## Decision

Use **Typer** as the CLI driving adapter. Commands live under `adapters/driving/cli/commands/`. Each command:

1. Parses arguments via Typer's type-hint-driven parameter declarations.
2. Constructs a `Principal` from the local token (read from a config file via the local config helper).
3. Calls exactly one use-case.
4. Formats output (human-readable by default; structured JSON when `--json` is passed).

A top-level `advisor` Typer app registers sub-apps for each command group: `validate`, `jobs`, `workspace`, `papers`, `share`, `config`, `admin`, `dev`. Admin and dev sub-apps are registered conditionally (see [0008 — One binary, role-gated](../../../decisions/0008-one-binary-role-gated.md)).

## Consequences

**Easy:**
- Command signatures read like ordinary Python functions with type hints; the framework derives flags and help text automatically.
- Adding a sub-command is one file under `commands/`.
- Output formatters are a small module (`adapters/driving/cli/formatters/`) shared across commands.

**Hard:**
- Typer's auto-derived behavior can surprise (e.g., an `Optional[str] = None` argument becomes a `--foo` flag, but a `str | None = None` may behave differently depending on version). Pin Typer and document conventions.
- Help-text role-gating (hide admin commands from non-admins) is not native Typer behavior. Implemented in the app's registration logic, conditional on the principal's role at startup.

**Forecloses:**
- Commands that do more than parse-call-format. The `--json` flag must work *because* the command does not interpret its result — it serializes the use-case's structured return value.

## Alternatives considered

- **Click** — viable. Same functionality, more boilerplate. Acceptable fallback if Typer's auto-derivation causes problems.
- **argparse** — rejected. Too much manual plumbing for the command count.
- **Hand-rolled** — rejected. Reinvents argument parsing badly.

## Review trigger

- Typer's auto-derivation causes a recurring pattern of bugs that disciplined Click code would not have. Migrate to Click.
- A second CLI framework feature is needed (interactive REPL, plugin system) that neither Typer nor Click supports. At that point the choice is "extend the framework" vs "ship a separate tool."
