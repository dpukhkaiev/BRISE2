<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderParaCoord } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'
import { trialsOfRegion } from '../../../../entities/experiment/lib/regions'
import type { SearchSpaceRegion } from '../../../../entities/experiment/model/experiment.model'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { specsByName, plotlyInstance } = storeToRefs(store)
const { allRes } = storeToRefs(plotStore)
const paraCoord = ref<HTMLElement | null>(null)
const props = defineProps<{
    region: SearchSpaceRegion
    paraCoordParams: string[]
    paraCoordObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!paraCoord.value) return
    // a trial of the region without a selected parameter is drawn as inactive in it
    const trials = trialsOfRegion(allRes.value, props.region)
    renderParaCoord(plotlyInstance.value, paraCoord.value, trials, props.paraCoordParams, props.paraCoordObjective, specsByName.value)
}

watch(
    [
        allRes, 
        () => props.paraCoordParams, 
        () => props.paraCoordObjective
    ],
    () => {
        render()
    },
    { deep: true }
)

// render once Plotly has finished loading; kept out of the deep watch above,
// which would otherwise traverse the whole Plotly object
watch(plotlyInstance, () => {
    render()
})

onBeforeUnmount(() => {
    if (paraCoord.value && plotlyInstance.value) {
        plotlyInstance.value.purge(paraCoord.value)
    }
})
</script>



<template>
  <div
    ref="paraCoord"
  />
</template>
