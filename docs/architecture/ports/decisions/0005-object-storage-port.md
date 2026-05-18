---
id: ports-0005
title: `ObjectStorage` port for large-blob storage
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The system stores binary blobs: paper PDFs, submitted figures, predicted figures, and similar attachments. These do not belong in the relational store; they are too large, immutable after upload, and naturally suited to object storage (filesystem in dev, S3-compatible in production).

Today, two backends are supported (`local` and `minio`) via a config flag, with both implementations sharing the same module and switching at function-call time. The shape is right; the wrapping is wrong (the if-else lives inside the call sites instead of being polymorphic).

A port makes this polymorphism explicit.

## Decision

```python
class ObjectStorage(Protocol):
    async def put(
        self,
        key: ObjectKey,
        data: bytes,
        *,
        content_type: str,
    ) -> None: ...

    async def get(self, key: ObjectKey) -> bytes: ...

    async def get_presigned_url(
        self,
        key: ObjectKey,
        *,
        expires_seconds: int = 3600,
    ) -> str: ...

    async def delete(self, key: ObjectKey) -> None: ...

    async def exists(self, key: ObjectKey) -> bool: ...
```

`ObjectKey` is a contract type (currently a `str`, kept as a distinct type for future evolution — e.g., bucket-scoped keys).

`get_presigned_url` is part of the port because the API serves blobs via presigned URLs (the frontend fetches them directly, not through the API process). Local-filesystem adapter implementation returns a path under `/static/attachments/` to be served by the web server; the call surface is identical.

## Consequences

**Easy:**
- Local-filesystem vs S3-compatible is an adapter swap. Production config switches; code does not.
- The figure-hydration logic (today buried in `pipeline_service.py`) calls `storage.get(...)` rather than knowing about filesystems or buckets.
- Tests use an in-memory dict-backed `ObjectStorage`.

**Hard:**
- Presigned URLs have very different semantics on local-filesystem vs S3. The local adapter returns a static-asset URL; the S3 adapter returns a signed URL with an expiry. Consumers must treat the returned URL as opaque and short-lived.
- Streaming-large-blob access (e.g., serving a 200MB PDF) is not in this port. If/when needed, add a streaming method; do not retrofit `get` to return a stream.

**Forecloses:**
- Direct filesystem or S3 SDK use anywhere outside `adapters/driven/object_storage/`.

## Adapters

- **`LocalObjectStorage`** — current default. Reads/writes under `backend/data/attachments/`. `get_presigned_url` returns a `/static/attachments/{key}` URL the API server hosts.
- **`MinioObjectStorage`** — current alternative. Configured via env. S3-compatible.

See [adapters/driven/decisions/0007-local-object-storage.md](../../adapters/driven/decisions/0007-local-object-storage.md) and [0008-minio-object-storage.md](../../adapters/driven/decisions/0008-minio-object-storage.md).

## Review trigger

- Streaming-large-blob access becomes required (e.g., serving multi-hundred-MB PDFs without buffering). Add `get_stream(...)`.
- Multi-tenancy: storage namespacing per workspace or user becomes a hard requirement. Adapt `ObjectKey` to a structured (bucket, path) or pre-namespace keys in the use-case layer.
- The figure-fetch path that currently does `httpx.get(url, ...)` for external image URLs (when a figure carries a `url` rather than an `object_key`) — that is *not* this port. It needs its own port (e.g., `ImageFetcher`) or to be folded in here as a `get_external(...)` method. Decide before relying on it heavily.
