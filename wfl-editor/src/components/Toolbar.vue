<script setup lang="ts">
import { useVueFlow } from '@vue-flow/core'
import { ref, markRaw, watch } from 'vue'
import { useGraphStore } from '../store.ts'


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

// TODO
function saveConfig(code: string) {

}

</script>

<template>
  <div class="toolbar">
    <button class="btn" v-for="node in nodeTypes" :key="node.type" :class="node.type" @click="addNode(node)">
      {{ node.label }}
    </button>
    <button class="btn" @click="saveConfig(code)">Save Configuration</button>
  </div>


</template>

<style>
.toolbar {
  position: absolute;
  top: 16px;
  left: 0;
  right: 0;
  width: 100%;
  transform: none;
  z-index: 50;
  height: 56px;
  background-color: rgba(8, 18, 43, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 0 24px;
  color: white;
}

.btn {
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  filter: brightness(1.05);
}

.btn:active {
  transform: translateY(0);
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