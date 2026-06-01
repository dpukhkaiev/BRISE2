<script setup lang="ts">
import { ref, markRaw } from 'vue'
// Vueflow
import type { Node, Edge } from '@vue-flow/core'
import { VueFlow, Panel, useVueFlow } from '@vue-flow/core'
// components
import Toolbar from './components/Toolbar.vue'
import NumberNode from './nodes/NumberNode.vue'
import CategoryNode from './nodes/CategoryNode.vue'
import Sidebar from './components/Sidebar.vue'

// desctructure nodes, edges here (no need of ref([]))
const { nodes, addEdges, onConnect, edges } = useVueFlow()

// bind types with .vue components
const myNodeTypes = {
  float: markRaw(NumberNode),
  integer: markRaw(NumberNode),
  nominal: markRaw(CategoryNode),
  ordinal: markRaw(CategoryNode)
}


// sidebar state
const activeNode = ref<any>(null)
const isSidebarOpen = ref(false)

onConnect((connection) => {
  addEdges(connection)
})

function onNodeClick(event: any) {
  // event.node gets information about the active node
  activeNode.value = event.node
  isSidebarOpen.value = true
}

function onPaneClick() {
  isSidebarOpen.value = false
  activeNode.value = null
}

function validateEdges(connection: any) {

  // find target and source nodes
  const sourceNode = nodes.value.find(node => node.id === connection.source)
  const targetNode = nodes.value.find(node => node.id === connection.target)

  // check if they exist
  if (sourceNode && targetNode) {
    if (sourceNode.type === 'float') {
      return false
    }
    if (sourceNode.type === 'integer') {
      return false
    }
  }
  return true
}

function generateWflCode() {
  const rawNodes = nodes.value
  const rawEdges = edges.value
  console.log(nodes.value)
  console.log(edges.value)
}
</script>

<template>
  <div style="height: 100vh; width: 100%; display: flex; flex-direction: column;">
    <VueFlow :nodes="nodes" :node-types="myNodeTypes" :is-valid-connection="validateEdges" @node-click="onNodeClick"
      @pane-click="onPaneClick">
      <Panel position="top-right" class="custom-center-panel">
        <Toolbar />
      </Panel>

    </VueFlow>

    <Sidebar :node="activeNode" :is-open="isSidebarOpen" @close="isSidebarOpen = false" />
  </div>

</template>

<style>
.custom-center-panel {
  position: absolute;
  top: 20px;
  left: 50%;
  right: auto !important;
  transform: translateX(-50%);
  margin: 0;
  z-index: 50;
}
</style>