<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'
import { VueFlow, useVueFlow, Edge } from '@vue-flow/core'

const props = defineProps<{
  id: string
  data: {
    name: string
  }

}>()
</script>

<template>
     <div class="category-box">
    <input
      v-model="$props.data.name"
      placeholder="Category Name"
      class="category-input" />
    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
     </div>
    </template>

<style>
.category-box {
  padding: 4px 8px;
  border: 1px dashed #64748b;
  border-radius: 6px;
  background: transparent;
}
.category-input {
  border: none;
  background: transparent;
  font-size: 12px;
  width: 100%;
  text-align: center;
}
</style>