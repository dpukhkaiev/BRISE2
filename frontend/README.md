# BRISE Frontend

## Tech Stack

- **Framework:** Vue 3 (`<script setup>`, Composition API) + TypeScript
- **UI:** Vuetify 3
- **State:** Pinia
- **Real-time transport:** RxJS + `@stomp/rx-stomp` / `@stomp/stompjs` (STOMP over WebSocket)
- **Charts:** modular `plotly.js` (only the core plus the trace types actually used are registered), lazy-loaded
  through `entities/main` into its own chunk
- **Build tool:** Vite
- **Testing:** Vitest + `@vue/test-utils` (jsdom environment) for unit tests, plus Vitest Browser Mode
  (Playwright/Chromium) for the chart runtime benchmarks
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
| `npm run build:analyze` | Same as `build`, plus a bundle-size report (`dist/stats.html`) |
| `npm run type-check` | Type-check only (`vue-tsc -b --noEmit`), without building |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Lint with ESLint (`eslint .`) |
| `npm run test` | Run the unit test suite in watch mode |
| `npm run test:run` | Run the unit test suite once |
| `npm run bench` | Run the chart runtime benchmarks (Vitest Browser Mode); needs a one-time `npx playwright install chromium` |

FSD layer-boundary rules are enforced via `eslint.config.ts` (using `eslint-plugin-boundaries`) and are
checked both by `npm run lint` and automatically by IDEs with ESLint integration.

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
├── tests/                # unit tests (test setup / shared test utilities, plus `tests_frontend_visualization/`
│                           for the chart widgets)
├── benchmarks/           # chart runtime benchmarks, run separately via `npm run bench`
├── App.vue
└── main.ts
```

Layer dependency rules (which layer may import from which) are enforced via `eslint-plugin-boundaries` — see the ESLint config for the exact ruleset.

## Real-time Data Flow

The frontend receives experiment updates via STOMP events (`DEFAULT`, `NEW`, `FINAL`, `PREDICTIONS`, `LOG`) dispatched through `entities/main`. Each chart/widget subscribes to the events it needs and derives its own view of the data (see `entities/experiment/lib/` for shared transformation logic).

## Charts

Which charts an experiment shows is decided by the product configuration's `PlotSelection` block (see
`main_node/Resources/example_plot_selection/` for an example); a chart with no matching `PlotSelection` entry is
never listed. Once an experiment is running, the "Visible charts" menu toggles which of the selected charts are
displayed. Most charts are computed client-side from measured trials, but Hyperparameter Importances, Contour and
Pareto Front are instead computed by `main-node` over the `main_plot_queue` RPC, so they need `main-node` running to
render.

## Waffle / Searchspace Editor Integration

The app bar (`src/App.vue`) links out to the two tools used to configure an experiment before it's run:

- **Open Searchspace Editor** — opens the [`searchspace_editor`](../searchspace_editor/README.md) app for visually designing the `SearchSpace` part of a Waffle `.wfl` model.
- **Open Waffle** — opens the  Waffle configuration wizard, where the full `.wfl` model is submitted to produce the product configuration JSON.

Both are driven by env vars read via `import.meta.env` (declared in `src/vite-env.d.ts`), alongside the event-service connection settings.

For local dev, these are supplied by the checked-in `frontend/.env` (defaulting to `localhost`, mirroring `deployment_settings/LocalDeployment.json`'s `Frontend` block). In Docker builds they're injected instead via the `BRISE_FRONTEND_*` build args set by `brise.sh` (see `Dockerfile`).

If `waffle` and/or `searchspace_editor` aren't running, these two links simply fail to load (the iframe stays blank, the external link 404s); the rest of the dashboard is unaffected.
