# SearchSpace Editor

A visual, canvas-based editor for authoring the **`SearchSpace`** part of a Waffle `.wfl` model —
numeric/categorical parameter nodes, hierarchical categories, drag-and-drop connections
, undo/redo, autosave to `localStorage`, and a live `.wfl` code preview
panel with copy/download buttons (downloads as `searchspace.wfl`).

## Tech Stack

- **Framework:** Vue 3 (`<script setup>`)
- **Canvas:** [Vue Flow](https://vueflow.dev/) (`@vue-flow/core`) for the node graph
- **State:** Pinia
- **Icons:** FontAwesome
- **Build tool:** Vite
- **Testing:** Vitest

## Requirements

- Node.js (check `.nvmrc`)

## Getting Started (local dev)

```bash
npm install
npm run dev
```

The app will be available at the local Vite dev server URL (printed in the terminal).

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with hot reload |
| `npm run build` | Build for production |
| `npm run preview` | Preview the production build locally |
| `npm run test` | Run the Vitest test suite in watch mode |
| `npm run test:run` | Run the Vitest test suite once |

## How It Fits Into the BRISE Workflow

This tool only produces the `SearchSpace` fragment of a Waffle model, built visually via the canvas.
It does **not** replace Waffle: the generated `.wfl` still needs to be manually inserted into a full model before that model is submitted to the Waffle
wizard, which walks the full staged-configuration process and emits the product configuration JSON. see [Waffle README.md](../waffle/README.md)  for the rest of that workflow.

## Docker / Integration

Served by docker-compose as the `searchspace-editor` service on port **3001**
([localhost:3001](http://localhost:3001)). It's also embedded as an iframe in the main BRISE dashboard's
"Open Searchspace Editor" tab (see [../frontend/README.md](../frontend/README.md) and
`frontend/src/App.vue`).
