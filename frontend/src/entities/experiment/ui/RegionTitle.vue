<script setup lang="ts">
import { regionLabel } from '../lib/regions'
import type { SearchSpaceRegion } from '../model/experiment.model'

defineOptions({ name: 'RegionTitle' })

defineProps<{
    region: SearchSpaceRegion
}>()
</script>

<template>
  <div class="text-subtitle-1 region-title">
    {{ regionLabel(region) }}
  </div>
</template>

<style scoped>
.region-title {
  margin: 10px
}
</style>
