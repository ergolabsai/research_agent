---
id: capabilities-knowledge-0003
title: Semantic Scholar lookup becomes its own port (proposed)
status: proposed
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The `Librarian` agent today calls Semantic Scholar's HTTP API directly from inside the agent code, often through the advisor MCP server's tooling. The call exists in two forms: a metadata lookup ("get this paper by id") and a search ("find papers matching this query").

This is structurally similar to the [LanceDB leak addressed by 0002](./0002-knowledge-store-port.md): an external service called directly from within a core service, with HTTP semantics leaking into the agent.

Three concrete pains:

1. Rate limits and retries are handled per call site, inconsistently.
2. Testing the Librarian requires either mocking the HTTP call or running against the real API.
3. If a second external lookup source is added (OpenAlex, CrossRef), the agent's structure does not accommodate it cleanly.

## Decision (proposed)

Declare a `PaperLookup` port that abstracts external paper-metadata lookups:

```python
class PaperLookup(Protocol):
    async def by_id(self, paper_id: PaperId) -> Paper | None: ...
    async def search(self, query: str, *, limit: int) -> list[Paper]: ...
```

Implement it with a `SemanticScholarPaperLookup` adapter (driven, in `adapters/driven/paper_lookup/semantic_scholar.py`). The Librarian receives the port in its constructor and calls only the port methods.

The port is distinct from `PaperIndex` because they serve different needs: `PaperIndex` is the *local* corpus; `PaperLookup` is *external on-demand*. A use-case may consult both — local first, then external for cites not found locally.

## Consequences

**Easy:**
- The Librarian's external-lookup logic moves behind a port; tests use a fake adapter that returns canned papers.
- A second external source (OpenAlex) is a second adapter that satisfies the same port, plus composition-layer choice of which to use.
- Rate-limit handling, retries, and API-key management live in the adapter, not scattered.

**Hard:**
- Some current call sites are inside MCP server tools, not in the Librarian directly. Those need to be re-routed: either the MCP server's tool becomes a thin wrapper that *calls* the port via the adapter, or the lookup moves out of MCP entirely into the agent. A decision is needed about whether external paper lookup is an MCP tool or a direct port call.

**Forecloses:**
- Direct `httpx.get("https://api.semanticscholar.org/...")` calls from inside core. Allowed only inside the adapter.

## Status: proposed, not yet accepted

This ADR is proposed because the change is structural — it requires re-routing existing call sites and deciding the MCP-tool-vs-direct-port question. Accepting requires:

1. Confirming `PaperLookup` is genuinely separate from `PaperIndex` (it is).
2. Deciding the MCP question: external-paper lookup as MCP tool, or as direct port call. Recommend direct port call; MCP tools are reserved for things that genuinely benefit from being available to LLMs as tools (the calculator does; metadata lookup mostly does not).

## Alternatives considered

- **Keep direct HTTP calls inside the Librarian** — rejected for the same reasons [0002](./0002-knowledge-store-port.md) rejected direct LanceDB calls.
- **Reuse `PaperIndex` for external lookups** — rejected. Different semantics: index is bulk-loaded, queryable; external lookup is on-demand, rate-limited, may fail.
- **Make external lookup an MCP tool only** — rejected as default. Couples a non-agent-facing capability to the LLM-tool ecosystem unnecessarily.

## Review trigger

- The proposal is accepted (status flips to `accepted`).
- A second external source materializes — at that point the port is the obvious place to handle source selection.
