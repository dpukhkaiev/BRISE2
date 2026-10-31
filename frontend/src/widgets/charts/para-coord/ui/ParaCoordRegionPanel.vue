<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ParaCoord from './ParaCoord.vue'
import RegionTitle from '../../../../entities/experiment/ui/RegionTitle.vue'
import type { SearchSpaceRegion } from '../../../../entities/experiment/model/experiment.model'

defineOptions({ name: 'ParaCoordRegionPanel' })

const props = defineProps<{
    region: SearchSpaceRegion
    showTitle: boolean
    paraCoordObjective: string
}>()

const regionParameters = computed(() => props.region.Parameters.map(parameter => parameter.Name))

const paraCoordParams = ref<string[]>([])
const selectedParaCoordParams = computed(() => {
    return paraCoordParams.value.length
        ? paraCoordParams.value
        : regionParameters.value.slice(0, 1)
})

// select all parameters of the region on initialization and new experiment description
watch(
    regionParameters,
    (parameters) => {
        paraCoordParams.value = [...parameters]
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
</style>
