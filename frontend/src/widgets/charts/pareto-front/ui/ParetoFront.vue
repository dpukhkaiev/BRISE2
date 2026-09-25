<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderParetoFront } from '../render'
import { storeToRefs } from 'pinia'
import { MainClientApi } from '../../../../entities/main/api/main.client.store'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description, plotlyInstance } = storeToRefs(store)
const paretofront = ref<HTMLElement | null>(null)

const props = defineProps<{
    paretoObjective1: string
    paretoObjective2: string
    onlyShowParetoFront: boolean
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!paretofront.value) return
    const result = await MainClientApi.calculatePlot(
        "pareto_front",
        {
            "experiment_description": experiment_description.value,
            "trials": allRes.value,
            "objective1": props.paretoObjective1,
            "objective2": props.paretoObjective2
        }
    )

    renderParetoFront(plotlyInstance.value, paretofront.value, result, props.onlyShowParetoFront)
}

watch(
    [
        allRes, 
        () => props.paretoObjective1, 
        () => props.paretoObjective2,
        () => props.onlyShowParetoFront
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
    if (paretofront.value && plotlyInstance.value) {
        plotlyInstance.value.purge(paretofront.value)
    }
})
</script>



<template>
  <div
    ref="paretofront"
  />
</template>