<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderHypImp } from '../render'
import { storeToRefs } from 'pinia'
import { MainClientApi } from '../../../../entities/main/api/main.client.store'
import { useMainEventStore } from '../../../../entities/main'
import { trialsOfRegion } from '../../../../entities/experiment/lib/regions'
import type { SearchSpaceRegion } from '../../../../entities/experiment/model/experiment.model'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { plotlyInstance } = storeToRefs(store)
const hypimp = ref<HTMLElement | null>(null)

const props = defineProps<{
    region: SearchSpaceRegion
    hypImpParams: string[]
    hypImpObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!hypimp.value) return
    // the plot service takes a requested parameter that a trial lacks as inactive in it
    const trials = trialsOfRegion(allRes.value, props.region)
    const result = await MainClientApi.calculatePlot(
        "hyperparameter_importances",
        {
            "trials": trials,
            "parameters": props.hypImpParams,
            "objective": props.hypImpObjective
        }
    )

    renderHypImp(plotlyInstance.value, hypimp.value, result)
}

watch(
    [
        allRes, 
        () => props.hypImpParams, 
        () => props.hypImpObjective
    ],
    () => {
        render()
    },
    { deep: true }
);

// render once Plotly has finished loading; kept out of the deep watch above,
// which would otherwise traverse the whole Plotly object
watch(plotlyInstance, () => {
    render()
})

onBeforeUnmount(() => {
    if (hypimp.value && plotlyInstance.value) {
        plotlyInstance.value.purge(hypimp.value)
    }
})
</script>



<template>
  <div
    ref="hypimp"
  />
</template>