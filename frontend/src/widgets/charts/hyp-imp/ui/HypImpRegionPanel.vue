<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import HypImp from './HypImp.vue'
import RegionTitle from '../../../../entities/experiment/ui/RegionTitle.vue'

defineOptions({ name: 'HypImpRegionPanel' })

const props = defineProps<{
    regionParameters: string[]
    showTitle: boolean
    hypImpObjective: string
}>()

const hypImpParams = ref<string[]>([])
const selectedHypImpParams = computed(() => {
    return hypImpParams.value.length
        ? hypImpParams.value
        : props.regionParameters.slice(0, 1)
})

// select all parameters of the region on initialization and new experiment description
watch(
    () => props.regionParameters,
    (parameters) => {
        hypImpParams.value = [...parameters]
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
          v-model="hypImpParams"
          :value="param"
          :label="param"
          density="compact"
          hide-details
          color="green-darken-2"
          :disabled="hypImpParams.length === 1 && hypImpParams.includes(param)"
        />
      </v-list-item>
    </v-list>
    <HypImp
      :hyp-imp-params="selectedHypImpParams"
      :hyp-imp-objective="hypImpObjective"
    />
  </div>
</template>

<style scoped>
.user-input {
  margin: 10px
}
</style>
