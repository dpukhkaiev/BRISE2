<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderParaCoord } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { experiment_description, plotlyInstance } = storeToRefs(store)
const { allRes } = storeToRefs(plotStore)
const paraCoord = ref<HTMLElement | null>(null)
const props = defineProps<{
    paraCoordParams: string[]
    paraCoordObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!paraCoord.value) return
    if (!experiment_description.value) 
        return
    renderParaCoord(plotlyInstance.value, paraCoord.value, allRes.value, props.paraCoordParams, props.paraCoordObjective, experiment_description.value)
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
