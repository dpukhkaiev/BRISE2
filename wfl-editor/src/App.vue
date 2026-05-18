<script setup lang="ts">
import { ref } from 'vue'
// Vueflow
import type { Node } from '@vue-flow/core'
import { VueFlow, Panel } from '@vue-flow/core'
// components
import Toolbar from './components/Toolbar.vue'
import NumberNode from './nodes/NumberNode.vue'
import CategoryNode from './nodes/CategoryNode.vue'
//styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// bind types with .vue components
const myNodeTypes = {
  float: 'GlobalNumberNode',
  integer: 'GlobalNumberNode',
  nominal: 'GlobalCategoryNode',
  ordinal: 'GlobalCategoryNode'
}

// start nodes array 
const nodes = ref([])

</script>

<template>
<div style="height: 100vh; width: 100%; display: flex; flex-direction: column;">
   <VueFlow :nodes="nodes" :node-types="myNodeTypes">
  <Panel>
    <Toolbar/>
  </Panel>

</VueFlow>
  </div>
  
</template>