<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'
import { VueFlow, useVueFlow } from '@vue-flow/core'

const props = defineProps<{
  id: string
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
    <div v-if="props.data.name" style="color: black; font-size: 14px;">{{ props.data.name }}</div>
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

.node-name {
  color: black,

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