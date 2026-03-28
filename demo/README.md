# Research Advisor Visual Demo

Standalone product demo that reuses the real app UI from `frontend/src` with an in-memory mocked API layer. No backend, auth server, or LLM runtime is required.

## What this demo includes

- Real landing/auth/app shell/dashboard/editor/validate pages from the production frontend.
- Full theme system and settings menu behavior identical to the main app.
- Mocked auth, documents, workspaces, sharing, attachments, user search, and pipeline endpoints.
- Simulated multi-step pipeline progress with deterministic final validation results.
- Fully isolated runtime in the `demo/` folder.

## Run locally

```bash
cd demo
npm install
npm run dev
```

Open: http://localhost:4174

## Build for preview

```bash
cd demo
npm run build
npm run preview
```

## Notes

- This is intentionally isolated from the main frontend/backend stack.
- API behavior is defined in `src/mocks/setupMockApi.ts`.
- The mock layer intercepts Axios calls at runtime and returns in-memory demo data.
