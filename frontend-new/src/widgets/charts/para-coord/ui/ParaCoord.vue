<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderParaCoord } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { experiment_description } = storeToRefs(store)
const { allRes } = storeToRefs(plotStore)
const paraCoord = ref<HTMLElement | null>(null)
const props = defineProps<{
    paraCoordParams: string[]
    paraCoordObjective: string
}>()

async function render() {
    await nextTick()

    if (!paraCoord.value) return
    if (!experiment_description.value) 
        return
    renderParaCoord(paraCoord.value, allRes.value, props.paraCoordParams, props.paraCoordObjective, experiment_description.value)
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
</script>



<template>
  <div
    ref="paraCoord"
  ></div>
</template>
