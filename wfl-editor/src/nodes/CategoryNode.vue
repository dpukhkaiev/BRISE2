<script setup lang="ts">
import { Position, Handle } from '@vue-flow/core'
import { computed } from 'vue'
//store
import { useGraphStore } from '../store.ts'

const props = defineProps<{
  id: string
  data: {
    label: string
    name: string
  }

}>()

const graphStore = useGraphStore()

function isValidTargetConnection(connection: any) {
  return !graphStore.hasParent(props.id)
}

const isDefaultOf = computed(() => {
  const defaultPath = graphStore.isDefaultOf(props.id)
  return defaultPath
})


</script>

<template>
  <div class="category-box" :class="{ 'is-default': isDefaultOf }">
    <div v-if="props.data.name" style="color: black; font-size: 11px;">{{ props.data.name }}</div>
    <Handle type="target" :position="Position.Top" :is-valid-connection="isValidTargetConnection" />
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


.category-box.is-default::after {
  content: 'Default';
  position: absolute;
  top: -12px;

  right: 6px;
  background: #eff6ff;

  color: #2563eb;

  border: 1px solid #bfdbfe;

  font-size: 8px;
  line-height: 2;
  padding: 0px 4px;
  border-radius: 2px;
  font-weight: 500;

}
</style>