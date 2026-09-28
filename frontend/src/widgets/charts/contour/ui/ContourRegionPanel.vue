<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import Contour from './Contour.vue'
import { useMainEventStore } from '../../../../entities/main'
import { regionLabel } from '../../../../entities/experiment/lib/regions'
import { findParameterSpec, isContourParameter } from '../../../../entities/experiment/lib/search-space'

defineOptions({ name: 'ContourRegionPanel' })

const props = defineProps<{
    regionParameters: string[]
    showTitle: boolean
    contourObjective: string
}>()

const store = useMainEventStore()
const { experiment_description } = storeToRefs(store)

// parameters of the region that can span a contour axis
const contourParameterNames = computed(() => {
    const description = experiment_description.value
    if (!description) {
        return []
    }
    return props.regionParameters.filter(param =>
        isContourParameter(findParameterSpec(description, param))
    )
})

const contourParam1 = ref("")
const contourParam2 = ref("")

// select the first two parameters of the region on initialization and new experiment description
watch(
    contourParameterNames,
    (params) => {
        contourParam1.value = params[0] ?? ""
        contourParam2.value = params[1] ?? ""
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
    <div
      v-if="contourParameterNames.length < 2"
      class="text-body-2 text-medium-emphasis region-title"
    >
      Not enough parameters in this region for a contour plot.
    </div>
    <template v-else>
      <v-select
        v-model="contourParam1"
        :items="contourParameterNames"
        label="Parameter 1"
        density="compact"
        variant="outlined"
        hide-details
        class="user-input"
      />
      <v-select
        v-model="contourParam2"
        :items="contourParameterNames"
        label="Parameter 2"
        density="compact"
        variant="outlined"
        hide-details
        class="user-input"
      />
      <Contour
        :contour-param1="contourParam1"
        :contour-param2="contourParam2"
        :contour-objective="contourObjective"
      />
    </template>
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
