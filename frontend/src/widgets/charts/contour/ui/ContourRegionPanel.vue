<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Contour from './Contour.vue'
import RegionTitle from '../../../../entities/experiment/ui/RegionTitle.vue'
import { isAxisParameter } from '../../../../entities/experiment/lib/search-space'
import type { SearchSpaceRegion } from '../../../../entities/experiment/model/experiment.model'

defineOptions({ name: 'ContourRegionPanel' })

const props = defineProps<{
    region: SearchSpaceRegion
    showTitle: boolean
    contourObjective: string
}>()

// parameters of the region that can span a contour axis
const contourParameterNames = computed(() =>
    props.region.Parameters.filter(isAxisParameter).map(parameter => parameter.Name)
)

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
    <RegionTitle
      v-if="showTitle"
      :region="region"
    />
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
