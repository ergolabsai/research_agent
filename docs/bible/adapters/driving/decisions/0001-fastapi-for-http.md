---
id: adapters-driving-0001
title: FastAPI as the HTTP driving adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The system needs an HTTP/JSON interface used by the React frontend and any external HTTP client. The mature Python options are FastAPI, Starlette (FastAPI's underlying framework), Django REST Framework, and Flask + extensions.

The selection criteria are: type-checked request/response models, async support, OpenAPI generation (the frontend's generated types depend on this), and ecosystem maturity.

## Decision

Use **FastAPI** as the HTTP driving adapter. Routes live in `adapters/driving/api/routes/`. Each route function:

1. Parses request body / query parameters via a Pydantic model.
2. Constructs a `Principal` (from JWT middleware that runs before the route).
3. Calls exactly one use-case (occasionally two for trivial composition).
4. Returns a Pydantic response model.

Authentication middleware decodes the JWT, builds the `Principal`, and attaches it to the request scope. A `Depends(get_principal)` dependency makes it available to routes.

## Consequences

**Easy:**
- Pydantic request/response models double as OpenAPI schema and as input to the frontend type generator.
- Type-checked at every boundary; mismatch between port contract and HTTP shape is caught at server start.
- Async-native, matches the port surface.

**Hard:**
- FastAPI's `Depends` system is tempting for things beyond `Principal` (e.g., resolving a `Document` from a path parameter). Resist: dependencies that *fetch* belong in use-cases, not in middleware.
- Errors raised by use-cases must be translated to HTTP responses. The translation table is in `adapters/driving/api/errors.py`. Drift between use-case exception types and HTTP mappings is a recurring bug source.

**Forecloses:**
- Routes doing more than parse-call-format. Even `if user.role == "admin"` belongs in the use-case, not in the route.

## Alternatives considered

- **Starlette directly** — rejected. Loses Pydantic integration and OpenAPI generation. FastAPI is Starlette plus the parts the project wants.
- **Django REST Framework** — rejected. Comes with Django's ORM, admin, and conventions that pull against hexagonal architecture.
- **Flask + extensions** — rejected. Async support is poor; the patchwork of plugins is fragile.

## Review trigger

- FastAPI's dependency-injection system starts being used for things beyond `Principal` resolution — at that point the boundary is leaking and either FastAPI's usage gets disciplined or the framework is reconsidered.
- A non-HTTP protocol (gRPC, GraphQL) becomes a primary surface. At that point a second driving adapter is added; FastAPI stays for what it serves.
