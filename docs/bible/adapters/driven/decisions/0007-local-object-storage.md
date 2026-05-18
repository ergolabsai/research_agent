---
id: adapters-driven-0007
title: Local filesystem as the default `ObjectStorage` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`ObjectStorage` ([port 0005](../../../ports/decisions/0005-object-storage-port.md)) needs at least one implementation. In dev and pre-alpha, the simplest backing store is the local filesystem; in production, S3-compatible (MinIO or AWS S3) is the path.

## Decision

Implement `ObjectStorage` with `LocalObjectStorage` that reads and writes files under `backend/data/attachments/` (configurable via env). Key → path is direct: `key=foo/bar.png` becomes `backend/data/attachments/foo/bar.png`.

`get_presigned_url` returns `/static/attachments/{key}` — a URL served by the API process via static-file mounting. Expiry is ignored (the URL never expires, since the static mount serves whatever exists).

Selected by `STORAGE_BACKEND=local` (the default).

## Consequences

**Easy:**
- Zero-ops storage in dev. Attachments are inspectable with `ls`.
- Backups are `tar` over the attachments directory.
- The static-mount URL works during dev without any signing infrastructure.

**Hard:**
- Static-mount URLs do not expire. Treating them as "presigned" is a soft fiction. Acceptable for dev/pre-alpha, *not* acceptable for production with sensitive content — switch to MinIO at that point.
- The API server's filesystem must have read/write access. In containerized deployments, this means a mounted volume.
- Horizontal scaling of the API does not work: each instance would have its own filesystem. Mitigated by switching to MinIO when scaling is on the table.

**Forecloses:**
- Multi-instance API deployment with local storage. The instances need a shared filesystem (NFS) or, more honestly, a switch to S3-compatible.

## Alternatives considered

- **Use MinIO even in dev** — viable; closer parity with prod. Rejected for the friction in dev (running MinIO locally, configuring keys). The port abstraction means the swap is cheap; running MinIO in dev becomes a choice the developer makes when they want parity.

## Review trigger

- Production deployment becomes imminent — switch composition to [MinIO](./0008-minio-object-storage.md).
- The API needs to run as more than one instance.
- Sensitive content storage requires URL expiry semantics that static mounts cannot provide.
