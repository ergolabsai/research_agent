# Research Advisor Visual Demo

Standalone product demo for visualizing the full advisor workflow with no backend, auth, or LLM runtime.

## What this demo includes

- Full 8-step advisor progress indicator with stage-by-stage status.
- PDF-like paper viewer pane (non-editable, presentation style).
- Right analysis sidebar with gated tools:
  - Plot Helper after figure evaluation completes.
  - Math Assistant after math evaluation completes.
  - Citation Review after citation scoring completes.
- Plot panel with true vs predicted plot and discrepancy comments.
- Math panel listing all equations and usage context with mock context updates and chat interaction.
- Citation panel with relevancy/convergence scores and expandable paper-level comparison notes.

## Run locally

```bash
cd demo
npm install
npm run dev
```

Open: http://localhost:5174

## Build for preview

```bash
cd demo
npm run build
npm run preview
```

## Notes

- This is intentionally isolated from the main frontend/backend stack.
- All content is mock fixture data in `src/data/fixtures.ts`.
- Use `Replay Demo` to reset and rerun the full process.
