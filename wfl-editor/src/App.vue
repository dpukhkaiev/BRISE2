<script setup lang="ts">
import { ref, markRaw } from 'vue'
// Vueflow
import type { Node } from '@vue-flow/core'
import { VueFlow, Panel } from '@vue-flow/core'
// components
import Toolbar from './components/Toolbar.vue'
import NumberNode from './nodes/NumberNode.vue'
import CategoryNode from './nodes/CategoryNode.vue'
import Sidebar from './components/Sidebar.vue'



// bind types with .vue components
const myNodeTypes = {
  float: markRaw(NumberNode),
  integer: markRaw(NumberNode),
  nominal: markRaw(CategoryNode),
  ordinal: markRaw(CategoryNode)
}

// start nodes array 
const nodes = ref([])

// sidebar state
const activeNode = ref<any>(null)
const isSidebarOpen = ref(false)


function onNodeClick(event: any) {
  // event.node gets information about the active node
  activeNode.value = event.node
  isSidebarOpen.value = true
}

function onPaneClick() {
  isSidebarOpen.value = false
  activeNode.value = null
}
</script>

<template>
  <div style="height: 100vh; width: 100%; display: flex; flex-direction: column;">
    <VueFlow :nodes="nodes" :node-types="myNodeTypes" @node-click="onNodeClick" @pane-click="onPaneClick">
      <Panel position="top-right">
        <Toolbar />
      </Panel>

    </VueFlow>

    <Sidebar :node="activeNode" :is-open="isSidebarOpen" @close="isSidebarOpen = false" />
  </div>

</template>