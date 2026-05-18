<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'
import { VueFlow, useVueFlow } from '@vue-flow/core'

const props = defineProps<{
  id: string
  type: string
  data: {
    label: string
  }

}>()

</script>

<template>
  <div :class="['node-base', type]">
    {{ props.data.label }}
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

.float {
  background-color: #fed7aa !important;
  color: #9a3412;
  border-color: #f97316;
}

.integer {
  background-color: #e0f2fe !important;
  color: #0369a1;
  border-color: #0284c7;
}
</style>