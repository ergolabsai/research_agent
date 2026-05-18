---
id: adapters-driven-0008
title: MinIO (S3-compatible) as the production `ObjectStorage` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The local-filesystem adapter ([0007](./0007-local-object-storage.md)) does not scale beyond one machine and has no real presigned-URL semantics. Production needs an S3-compatible backend. The two paths are MinIO (self-hosted on the dedicated server) and AWS S3 (managed).

For a dedicated-server deployment with bounded cost, self-hosted MinIO is the default. AWS S3 stays available as a drop-in (same S3 API).

## Decision

Implement `ObjectStorage` with `MinioObjectStorage` using the `minio` Python client. Selected by `STORAGE_BACKEND=minio` (or `s3` — same adapter, different endpoint).

The adapter handles:

- Bucket creation on startup (`init_storage()` ensures the bucket exists).
- Presigned URL generation with real expiry semantics.
- Multipart upload for large blobs (above a threshold).

Configured via env vars: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE` (TLS).

## Consequences

**Easy:**
- Multi-instance API deployment works: all instances see the same bucket.
- Presigned URLs have real expiry — sensitive content is not freely browsable forever.
- S3 API compatibility means switching to AWS S3 (or DigitalOcean Spaces, etc.) is a config change.

**Hard:**
- Running MinIO is one more service. Self-hosted means systemd or Docker Compose; managed (AWS) shifts the cost.
- Backups are no longer a `tar`. Either rely on the storage service's replication or run periodic syncs.
- Local dev still wants the filesystem adapter for friction reasons. Two adapters maintained, both first-class.

**Forecloses:**
- Treating storage as "just a directory." MinIO is a service with availability and capacity properties.

## Alternatives considered

- **AWS S3 directly** — viable; identical client, different endpoint. Choice between self-hosted MinIO and managed S3 is a deployment concern, not an adapter concern.
- **A different self-hosted object store (Ceph, Garage)** — overkill for current scale.

## Review trigger

- Storage volume or availability requirements outgrow what self-hosted MinIO on a single dedicated server can provide.
- Compliance or geo-replication needs require managed object storage.
