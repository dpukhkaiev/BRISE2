<script setup="ts">
import { ref } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'

// Importiere die Standard-Styles von Vue Flow
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// Test-Daten für deine Hyperparameter-Boxen (Nodes)
const nodes = ref([
  {
    id: '1',
    type: 'default',
    label: 'frequency : OrdinalHyperparameter',
    position: { x: 100, y: 100 },
    style: { background: '#fef08a', border: '1px solid #eab308', borderRadius: '8px' },
  },
  {
    id: '2',
    type: 'default',
    label: 'threads : OrdinalHyperparameter',
    position: { x: 400, y: 150 },
    style: { background: '#fed7aa', border: '1px solid #f97316', borderRadius: '8px' },
  },
])

// Verbindungen (Edges) zwischen den Parametern
const edges = ref([
  { id: 'e1-2', source: '1', target: '2', animated: true }
])

// Zustand für die einklappbare lila Sidebar
const isSidebarOpen = ref(true)
</script>

<template>
  <div class="editor-container">
    <div class="canvas-area">
      <VueFlow :nodes="nodes" :edges="edges" fit-view-on-init>
        <Background pattern-color="#aaa" :gap="16" />
        <Controls />
      </VueFlow>
    </div>

    <div :class="['sidebar', { 'sidebar-closed': !isSidebarOpen }]">
      <button class="toggle-btn" @click="isSidebarOpen = !isSidebarOpen">
        {{ isSidebarOpen ? '▶' : '◀' }}
      </button>

      <div v-if="isSidebarOpen" class="sidebar-content">
        <h3>Configuration</h3>
        <p>Hier kommt die geordnete Kategorien-Tabelle hin!</p>
      </div>
    </div>
  </div>
</template>

<style>
/* Schnelles CSS für das Layout */
html,
body,
#app {
  margin: 0;
  width: 100%;
  height: 100%;
  font-family: sans-serif;
}

.editor-container {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.canvas-area {
  flex-grow: 1;
  height: 100%;
}

.sidebar {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  width: 300px;
  background-color: #b4b6e5;
  /* Dein Lila */
  transition: transform 0.3s ease;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.sidebar-closed {
  transform: translateX(100%);
}

.toggle-btn {
  position: absolute;
  left: -30px;
  top: 50%;
  transform: translateY(-50%);
  background: #b4b6e5;
  border: none;
  padding: 10px 8px;
  cursor: pointer;
  border-radius: 4px 0 0 4px;
}

.sidebar-content {
  padding: 20px;
}
</style>