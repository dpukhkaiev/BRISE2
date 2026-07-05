<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'
import { VueFlow, useVueFlow, Edge } from '@vue-flow/core'
//store
import { useGraphStore } from '../store.ts'

const props = defineProps<{
  id: string
  type: string
  data: {
    label: string
    name: string
  }

}>()

const graphStore = useGraphStore()

function isValidTargetConnection(connection: any) {
  return !graphStore.hasParent(props.id)
}

</script>

<template>
  <div :class="['node-base', type]">
    {{ props.data.label }}
    <div v-if="props.data.name" style="color: black; font-size: 11px;">{{ props.data.name }}</div>
    <Handle type="target" :position="Position.Top" id="target-n" :is-valid-connection="isValidTargetConnection" />

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