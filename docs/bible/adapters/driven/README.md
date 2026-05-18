# Driven adapters

Implementations of [driven ports](../../ports/). Each adapter satisfies exactly one port. The adapter knows about a specific piece of infrastructure (Anthropic, LanceDB, SQLite, etc.); the port and its callers do not.

## Adapters in this folder

Grouped by the port each satisfies. Multiple adapters per port is normal — the composition layer picks which is active.

### LLM (`LLMClient`)
| Adapter | Status |
|---|---|
| [Anthropic](./decisions/0001-anthropic-llm-adapter.md) | accepted (default) |
| [OpenRouter](./decisions/0002-openrouter-llm-adapter.md) | accepted (alternative) |

### Paper Index (`PaperIndex`)
| Adapter | Status |
|---|---|
| [LanceDB](./decisions/0003-lancedb-paper-index.md) | accepted |

### Calculator (`Calculator`)
| Adapter | Status |
|---|---|
| [MCP calculator client](./decisions/0004-mcp-calculator-client.md) | accepted |

### Job Store (`JobStore`)
| Adapter | Status |
|---|---|
| [SQLite](./decisions/0005-sqlite-job-store.md) | accepted (pre-alpha) |
| [Postgres](./decisions/0006-postgres-job-store.md) | proposed (Step 3 of migration) |

### Object Storage (`ObjectStorage`)
| Adapter | Status |
|---|---|
| [Local filesystem](./decisions/0007-local-object-storage.md) | accepted (default) |
| [MinIO / S3-compatible](./decisions/0008-minio-object-storage.md) | accepted (production option) |

### Persistence shape
| Adapter | Status |
|---|---|
| [No Alembic yet](./decisions/0009-no-alembic-yet.md) | accepted (transitional) |

### Identity (`TokenIssuer`, `PasswordHasher`)
| Adapter | Status |
|---|---|
| [python-jose token issuer](./decisions/0010-jose-token-issuer.md) | accepted |
| [bcrypt password hasher](./decisions/0011-bcrypt-password-hasher.md) | accepted |

### Time (`Clock`)
| Adapter | Status |
|---|---|
| [System clock (America/Los_Angeles)](./decisions/0012-system-clock.md) | accepted |

### Repositories (`{User,Workspace,Document,Attachment}Repository`)
| Adapter | Status |
|---|---|
| [SQLite repositories via SQLModel](./decisions/0013-sqlite-repositories.md) | accepted |

## Convention: one adapter, one file, one ADR

Each adapter implementation is one module (or one cohesive submodule) and has exactly one ADR. When the adapter is replaced, the ADR is superseded by a new one — never edited in place.
