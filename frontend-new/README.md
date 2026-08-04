# BRISE Frontend (frontend-new)

A Vue 3 rewrite of the legacy BRISE Angular frontend — a live dashboard for monitoring [BRISE2](https://github.com/dpukhkaiev/BRISE2) 

## Tech Stack

- **Framework:** Vue 3 (`<script setup>`, Composition API) + TypeScript
- **UI:** Vuetify 3
- **State:** Pinia
- **Real-time transport:** RxJS + `@stomp/rx-stomp` / `@stomp/stompjs` (STOMP over WebSocket)
- **Charts:** Plotly.js (`plotly.js-dist-min`, lazy-loaded, bundled into its own chunk)
- **Build tool:** Vite
- **Testing:** Vitest + `@vue/test-utils` (jsdom environment)
- **Architecture:** Feature-Sliced Design (FSD) — layer boundaries enforced via `eslint-plugin-boundaries`

## Requirements

- Node.js (check `.nvmrc`)
- A running instance of the BRISE `main-node` backend, running as its **own Docker container** 
- The frontend connects to `main-node` over STOMP/WebSocket


Start the whole stack from the BRISE repository root:
 
```bash
./brise.sh up -m docker-compose
```
 
Then reach the frontend at [localhost](http://localhost/) (port 80). The frontend connects to `main-node`'s events via the `event_service` (RabbitMQ/STOMP), so `event_service` and `main-node` both need to be up for live data to appear.
 
## Getting Started (local dev, without Docker)

```bash
npm install
npm run dev
```

The app will be available at the local Vite dev server URL (printed in the terminal, `http://localhost:5173`).

> The frontend expects `main-node` to be running and reachable; without it, the dashboard will load but stay empty (no experiment data, no charts) until a connection is established.

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with hot reload |
| `npm run build` | Type-check (`vue-tsc -b`) and build for production |
| `npm run preview` | Preview the production build locally |
| `npm run test` | Run the Vitest test suite in watch mode |


> **Note:** there is currently no `npm run lint` script. FSD layer-boundary rules are enforced via `eslint.config.ts` (using `eslint-plugin-boundaries`) and are picked up automatically by IDEs with ESLint integration. 

## Project Structure

The codebase follows **Feature-Sliced Design (FSD)**:

```
src/
├── entities/          # domain logic, shared across features (data models, transformers)
│   ├── experiment/     # experiment-domain helpers (e.g. heatmap data transform, label resolution)
│   ├── main/            # main event store (STOMP subscriptions, experiment_description, searchspace)
│   └── task/             # task/solution data models
├── features/          # user-facing features (e.g. download-popup)
├── widgets/            # composed UI blocks built from entities/features (e.g. charts, launch control bar, info board)
├── shared/               # generic, domain-agnostic utilities
├── tests/                # test setup / shared test utilities
├── App.vue
├── main.ts
└── usePerformance.ts   # performance measurement composable
```

Layer dependency rules (which layer may import from which) are enforced via `eslint-plugin-boundaries` — see the ESLint config for the exact ruleset.

## Real-time Data Flow

The frontend receives experiment updates via STOMP events (`DEFAULT`, `NEW`, `FINAL`, `PREDICTIONS`, `LOG`) dispatched through `entities/main`. Each chart/widget subscribes to the events it needs and derives its own view of the data (see `entities/experiment/lib/` for shared transformation logic).


## Known Issues

- Restarting an experiment generally works through the UI, but after repeated runs (~5–10 experiments) in one session, the `main-node` backend accumulates stale state that a normal restart doesn't clear (symptoms: experiment name stops displaying, charts sometimes fail to render). Currently only a full Docker rebuild/restart of `main-node` resolves this.



