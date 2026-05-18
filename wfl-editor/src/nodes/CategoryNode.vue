<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'

// define node structure
defineProps<{
  type: string
  data: {
    label: string
  }

}>()
</script>

<template>
  <div :class="['node-base', type]">
    {{ data.label }}
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<style>
.node-base {
  padding: 8px 14px;
  border: 1px solid;
  border-radius: 6px;
  font-weight: 600;
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