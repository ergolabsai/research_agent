---
id: capabilities-collaboration-0003
title: Last-write-wins for concurrent document edits
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

When two users edit the same document at the same time, three families of behavior are possible:

- **Last-write-wins** — the most recent save overwrites the earlier one. Simple. The user whose write loses is silently overridden unless the UI shows the conflict.
- **Optimistic locking** — each write carries a version token; conflicting writes fail and the UI prompts the user to merge.
- **Operational transform / CRDT** — both writes are merged automatically into a coherent state, character-by-character. Real-time collaborative editing.

The cost of OT/CRDT is large: a new server-side component, careful client-side state management, an entirely different sync protocol. The benefit only pays off when concurrent editing is a frequent, expected user behavior.

## Decision

Document edits are **last-write-wins**. Concurrent edits are not prevented by the server; the most recent `UpdateDocument` call replaces the document body in full.

The client *may* show a soft conflict indicator if it detects that the document has changed since the user started editing, but the server's behavior is unconditional acceptance of the latest write.

## Consequences

**Easy:**
- The data model is trivially simple: `documents.content` is replaced as a whole on each save.
- No version tokens, no conflict resolution UI on the server, no CRDT runtime.
- Backups are uncomplicated: a snapshot is one row.

**Hard:**
- If two users are editing the same document simultaneously, one user's work can silently disappear. This is *intentional* for the current scale — collaborative editing is not yet the primary mode — but it is a real cost.
- A "version history" feature is not provided by the data model; it would require introducing a `DocumentRevision` table or similar.

**Forecloses:**
- Real-time collaborative editing as currently structured. Adding it later is a major change to both data model and sync protocol.
- Atomic "merge two users' edits" without OT/CRDT.

## Alternatives considered

- **Optimistic locking with conflict-on-save UI** — viable as an incremental upgrade. The data model adds `version` (or a `last_modified` timestamp the client carries); the server rejects writes when the token is stale; the client UI prompts. Reasonable next step if conflicts become common enough to be a real complaint, but well short of CRDT complexity.
- **CRDT / OT (e.g., Yjs)** — rejected at current stage. Real-time collaborative editing is not a product requirement now, and the implementation cost is large.
- **Server-side merge of plain-text edits** — rejected. Merge conflicts on prose are a worse UX than just losing a change.

## Review trigger

- A user reports lost work due to a silent overwrite. Two paths: introduce optimistic locking and a conflict prompt (lower investment), or commit to real-time editing (full CRDT).
- Concurrent editing becomes a frequent expected behavior (e.g., a team is co-authoring a paper review). At that point CRDT or OT becomes warranted.
