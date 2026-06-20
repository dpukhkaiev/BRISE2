<script setup lang="ts">
import { Position, Handle, Edge } from '@vue-flow/core'

// define node structure
const props = defineProps<{
  type: string
  data: {
    label: string
    name: string
  }

}>()
</script>

<template>
  <div :class="['node-base', type]">
    {{ props.data.label }}
    <div v-if="props.data.name" style="color: black; font-size: 11px;">{{ props.data.name }}</div>
    <Handle type="target" :position="Position.Top" id="target-c"/>
    <Handle type="source" :position="Position.Bottom" id="source-c" />
  
  </div>
</template>

<style>
.node-base {
  padding: 4px 8px;
  border: 1px solid;
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
}

.ordinal {
  background-color: #fef9c3 !important;
  color: #854d0e;
  border-color: #ca8a04;
}

.nominal {
  background-color: #dcfce7 !important;
  color: #166534;
  border-color: #16a34a;
}
</style>