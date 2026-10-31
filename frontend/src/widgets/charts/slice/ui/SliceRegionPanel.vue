<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Slice from './Slice.vue'
import RegionTitle from '../../../../entities/experiment/ui/RegionTitle.vue'
import type { SearchSpaceRegion } from '../../../../entities/experiment/model/experiment.model'

defineOptions({ name: 'SliceRegionPanel' })

const props = defineProps<{
    region: SearchSpaceRegion
    showTitle: boolean
    sliceObjective: string
}>()

const regionParameters = computed(() => props.region.Parameters.map(parameter => parameter.Name))

const sliceParam = ref("")

// select the first parameter of the region on initialization and new experiment description
watch(
    regionParameters,
    (parameters) => {
        sliceParam.value = parameters[0] ?? ""
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
</style>
