# Frontend

The React web app — itself a [driving adapter](../adapters/driving/decisions/0003-react-mui-for-web.md) on top of the HTTP API. The frontend has enough of its own internal architecture (state management, theming, routing, type generation) to deserve its own folder of ADRs.

This folder covers frontend-internal decisions. The decision to *use React + MUI + Vite* as the adapter lives under [adapters/driving/0003](../adapters/driving/decisions/0003-react-mui-for-web.md); this folder's ADRs are about what happens *inside* the frontend.

## ADRs in this folder

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-vite-spa.md) | Vite + SPA shape | accepted |
| [0002](./decisions/0002-mui-themes.md) | MUI themes with localStorage persistence | accepted |
| [0003](./decisions/0003-state-via-context-only.md) | React Context for state; no external state library | accepted |
| [0004](./decisions/0004-generated-types-from-contracts.md) | Frontend types generated from Pydantic contracts | proposed |
