<script setup lang="ts">
import { regionLabel } from '../lib/regions'

defineOptions({ name: 'RegionTitle' })

defineProps<{
    regionParameters: string[]
}>()
</script>

<template>
  <div class="text-subtitle-1 region-title">
    {{ regionLabel(regionParameters) }}
  </div>
</template>

<style scoped>
.region-title {
  margin: 10px
}
</style>
