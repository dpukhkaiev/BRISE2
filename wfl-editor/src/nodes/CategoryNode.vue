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
    <input v-model="$props.data.name" class="category-input" />
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
  top: -9px;
  /* Leicht angepasst für den feineren Look */
  right: 6px;
  background: #eff6ff;
  /* Sehr sanftes, helles Hintergrund-Blau */
  color: #2563eb;
  /* Gut lesbares, aber unaufdringliches Text-Blau */
  border: 1px solid #bfdbfe;
  /* Feiner Rahmen um das Label herum */
  font-size: 8px;
  /* Etwas kleiner und dezenter */
  padding: 0px 4px;
  /* Flacheres Padding für einen "humble" Look */
  border-radius: 3px;
  font-weight: 500;
  /* Nicht ganz so fetter Text */
}
</style>