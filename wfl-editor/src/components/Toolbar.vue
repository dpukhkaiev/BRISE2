<script setup lang="ts">
import { useVueFlow } from '@vue-flow/core'
import { useGraphStore } from '../store.ts'
import { storeToRefs } from 'pinia'

const { addNodes } = useVueFlow()

const nodeTypes = [
  { type: 'float', label: 'FloatHyperparameter' },
  { type: 'ordinal', label: 'OrdinalHyperparameter' },
  { type: 'nominal', label: 'NominalHyperparameter' },
  { type: 'integer', label: 'IntegerHyperparameter' },
]

const graphStore = useGraphStore()
// add nodes with parameters
function addNode(nodeConfig: { type: string, label: string }) {
  const node = graphStore.createNode(nodeConfig)
  addNodes(node)
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
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;

  height: 50px;
  background-color: #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
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