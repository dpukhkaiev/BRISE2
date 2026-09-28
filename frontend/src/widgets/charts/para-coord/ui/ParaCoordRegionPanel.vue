<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ParaCoord from './ParaCoord.vue'
import { regionLabel } from '../../../../entities/experiment/lib/regions'

defineOptions({ name: 'ParaCoordRegionPanel' })

const props = defineProps<{
    regionParameters: string[]
    showTitle: boolean
    paraCoordObjective: string
}>()

const paraCoordParams = ref<string[]>([])
const selectedParaCoordParams = computed(() => {
    return paraCoordParams.value.length
        ? paraCoordParams.value
        : props.regionParameters.slice(0, 1)
})

// select all parameters of the region on initialization and new experiment description
watch(
    () => props.regionParameters,
    (parameters) => {
        paraCoordParams.value = [...parameters]
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
    <v-list
      density="compact"
      min-width="180"
      class="user-input"
    >
      <v-list-subheader>Parameters</v-list-subheader>
      <v-list-item
        v-for="param in regionParameters"
        :key="param"
      >
        <v-checkbox
          v-model="paraCoordParams"
          :value="param"
          :label="param"
          density="compact"
          hide-details
          color="green-darken-2"
          :disabled="paraCoordParams.length === 1 && paraCoordParams.includes(param)"
        />
      </v-list-item>
    </v-list>
    <ParaCoord
      :para-coord-params="selectedParaCoordParams"
      :para-coord-objective="paraCoordObjective"
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
