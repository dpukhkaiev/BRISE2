<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderOptHist } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { experiment_description, plotlyInstance } = storeToRefs(store)
const { allRes, solution } = storeToRefs(plotStore)
const optHist = ref<HTMLElement | null>(null)
const props = defineProps<{
    optHistObjective: string
}>();

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!optHist.value) return
    if (!experiment_description.value) 
        return
    renderOptHist(plotlyInstance.value, optHist.value, allRes.value, experiment_description.value, props.optHistObjective, solution.value)
}

watch(
    [
        allRes, 
        solution,
        () => props.optHistObjective
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
    if (optHist.value && plotlyInstance.value) {
        plotlyInstance.value.purge(optHist.value)
    }
})
</script>



<template>
  <div
    ref="optHist"
  />
</template>