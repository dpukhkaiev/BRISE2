<script setup lang="ts">
import { ref, watch } from 'vue'
import Slice from './Slice.vue'
import { regionLabel } from '../../../../entities/experiment/lib/regions'

defineOptions({ name: 'SliceRegionPanel' })

const props = defineProps<{
    regionParameters: string[]
    showTitle: boolean
    sliceObjective: string
}>()

const sliceParam = ref("")

// select the first parameter of the region on initialization and new experiment description
watch(
    () => props.regionParameters,
    (parameters) => {
        sliceParam.value = parameters[0] ?? ""
    },
    { immediate: true }
)
</script>

<template>
  <div>
    <div
      v-if="showTitle"
      class="text-subtitle-1 region-title"
    >
      {{ regionLabel(regionParameters) }}
    </div>
    <v-select
      v-model="sliceParam"
      :items="regionParameters"
      label="Parameter"
      density="compact"
      variant="outlined"
      hide-details
      class="user-input"
    />
    <Slice
      :slice-param="sliceParam"
      :slice-objective="sliceObjective"
    />
  </div>
</template>

<style scoped>
.user-input {
  margin: 10px
}
.region-title {
  margin: 10px
}
</style>
