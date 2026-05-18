# Capability: Collaboration

The "Notion-like" half of the system. Users create documents, organize them in workspaces, share with other users, and attach files (including papers to be validated).

This capability is what *gets* a paper in front of the [validation](../validation/) pipeline in the first place — and what holds the user's working environment between sessions.

## Concepts

- **User** — a person with credentials (or a guest with an ephemeral identity). Owned by [identity](../identity/); referenced here.
- **Workspace** — a named container for documents. Has an owner, members, and a sharing model.
- **Workspace member** — a `User` granted access to a `Workspace`, with a role (owner, editor, viewer).
- **Document** — a user-created piece of content. Lives inside a workspace (or in the user's personal scope). Has title, content (markdown or rich text), timestamps.
- **Document share** — a direct grant of access to a specific document, independent of workspace membership. Used for "share this one paper with X" flows.
- **Attachment** — a file (typically PDF or image) associated with a document. Stored via the `ObjectStorage` port; metadata in the relational store.

The relationship between a document and a *paper* (the validation capability's central concept) is intentional and minimal: a document may attach a paper, and a validation job references the document it came from. Validation operates on the paper, not the document.

## Use-cases this capability exposes

(Once migration is complete, each lives as a file under `core/use_cases/collaboration/`.)

- `CreateDocument`, `UpdateDocument`, `DeleteDocument`, `GetDocument`, `ListDocuments`
- `CreateWorkspace`, `UpdateWorkspace`, `DeleteWorkspace`, `GetWorkspace`, `ListWorkspaces`
- `AddWorkspaceMember`, `RemoveWorkspaceMember`, `UpdateMemberRole`
- `ShareDocument`, `UnshareDocument`, `ListDocumentShares`
- `UploadAttachment`, `DeleteAttachment`, `GetAttachmentUrl`

Each use-case takes a `Principal` as its first argument ([architecture/0005](../../architecture/decisions/0005-principal-in-every-usecase.md)) and performs ownership / membership checks.

## Ports this capability depends on

- [`DocumentRepository`](../../ports/decisions/0009-repository-ports.md) — persist documents and queries.
- [`WorkspaceRepository`](../../ports/decisions/0009-repository-ports.md) — persist workspaces and membership.
- [`UserRepository`](../../ports/decisions/0009-repository-ports.md) — look up users referenced as members or owners.
- [`ObjectStorage`](../../ports/decisions/0005-object-storage-port.md) — attachment file bytes.
- [`Clock`](../../ports/decisions/0008-clock-port.md) — timestamps.

## Authorization model

A simple matrix today (subject to future refinement):

| Action | Required relationship |
|---|---|
| View document | Owner OR workspace member (if in workspace) OR explicit share recipient |
| Edit document | Owner OR workspace editor/owner OR explicit share with edit grant |
| Delete document | Owner OR workspace owner |
| View workspace | Owner OR any member |
| Manage workspace members | Owner |
| Delete workspace | Owner |

Checks are performed inside each use-case via the `authz` helper, with the relationship lookup going through the relevant repository port.

## What this capability is *not*

- Not real-time collaborative editing. There is no operational-transform or CRDT layer. Concurrent edits are last-write-wins, intentionally, for now.
- Not a permissions system in its own right. It uses [identity](../identity/)'s `Principal` and `Permission`; it does not define new permissions beyond ownership/membership relations.
- Not a file storage system. It uses the `ObjectStorage` port; the bytes live elsewhere.

## ADRs in this capability

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-workspace-membership-model.md) | Workspace membership model | accepted |
| [0002](./decisions/0002-document-sharing-model.md) | Document sharing model | accepted |
| [0003](./decisions/0003-last-write-wins.md) | Last-write-wins for concurrent edits | accepted |
