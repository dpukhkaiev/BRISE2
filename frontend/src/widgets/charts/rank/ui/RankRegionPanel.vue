<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import Rank from './Rank.vue'
import { useMainEventStore } from '../../../../entities/main'
import RegionTitle from '../../../../entities/experiment/ui/RegionTitle.vue'
import { findParameterSpec, isAxisParameter } from '../../../../entities/experiment/lib/search-space'

defineOptions({ name: 'RankRegionPanel' })

const props = defineProps<{
    regionParameters: string[]
    showTitle: boolean
    rankObjective: string
}>()

const store = useMainEventStore()
const { experiment_description } = storeToRefs(store)

// parameters of the region that can span a rank axis
const rankParameterNames = computed(() => {
    const description = experiment_description.value
    if (!description) {
        return []
    }
    return props.regionParameters.filter(param =>
        isAxisParameter(findParameterSpec(description, param))
    )
})

const rankParam1 = ref("")
const rankParam2 = ref("")

// each axis offers every parameter except the one chosen for the other axis
const rankParam1Items = computed(() => rankParameterNames.value.filter(param => param !== rankParam2.value))
const rankParam2Items = computed(() => rankParameterNames.value.filter(param => param !== rankParam1.value))

// select the first two parameters of the region on initialization and new experiment description
watch(
    rankParameterNames,
    (params) => {
        rankParam1.value = params[0] ?? ""
        rankParam2.value = params[1] ?? ""
    },
    { immediate: true }
)
</script>

<template>
  <div>
    <RegionTitle
      v-if="showTitle"
      :region-parameters="regionParameters"
    />
    <div
      v-if="rankParameterNames.length < 2"
      class="text-body-2 text-medium-emphasis region-message"
    >
      Not enough parameters in this region for a rank plot.
    </div>
    <template v-else>
      <v-select
        v-model="rankParam1"
        :items="rankParam1Items"
        label="Parameter 1"
        density="compact"
        variant="outlined"
        hide-details
        class="user-input"
      />
      <v-select
        v-model="rankParam2"
        :items="rankParam2Items"
        label="Parameter 2"
        density="compact"
        variant="outlined"
        hide-details
        class="user-input"
      />
      <Rank
        :rank-param1="rankParam1"
        :rank-param2="rankParam2"
        :rank-objective="rankObjective"
      />
    </template>
  </div>
</template>

<style scoped>
.user-input {
  margin: 10px
}
.region-message {
  margin: 10px
}
</style>
