<script setup lang="ts">
import { VueFlow, useVueFlow } from '@vue-flow/core'

const { addNodes } = useVueFlow()

// define node types
const nodeTypes = [
  { type: 'float', label: 'FloatHyperParameter' },
  { type: 'ordinal', label: 'OrdinalHyperParameter' },
  { type: 'nominal', label: 'NominalHyperParameter' },
  { type: 'integer', label: 'IntegerHyperParameter' },
]

// add nodes with parameters
function addNode(nodeConfig: { type: string, label: string }) {
  const id = Date.now().toString()
  const categories = nodeConfig.type === 'nominal' || nodeConfig.type === 'ordinal' ? [] : undefined
  addNodes({
    id: id,
    type: nodeConfig.type,
    position: { x: Math.random() * 500, y: Math.random() * 500 },
    data: { label: nodeConfig.label, name: '', categories: categories ? [] : undefined }
  })
  console.log('id: ', id)
}
</script>

<template>
  <div class="toolbar">
    <button class="btn" v-for="node in nodeTypes" :key="node.type" :class="node.type" @click="addNode(node)">
      {{ node.label }}
    </button>
  </div>
</template>

<style scoped>
.toolbar {
  height: 50px;
  background-color: #1e293b;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 0 20px;
  color: white;
}

.btn {
  padding: 6px 14px;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}


.ordinal {
  background-color: #fef9c3;
  color: #854d0e;
  border-color: #ca8a04;
}


.nominal {
  background-color: #dcfce7;
  color: #166534;
  border-color: #16a34a;
}

.float {
  background-color: #fed7aa;
  color: #9a3412;
  border-color: #f97316;
}

.integer {
  background-color: #e0f2fe;
  color: #0369a1;
  border-color: #0284c7;
}
</style>