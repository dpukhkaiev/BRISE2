<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderContour } from '../render'
import { storeToRefs } from 'pinia'
import { MainClientApi } from '../../../../entities/main/api/main.client.store'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const contour = ref<HTMLElement | null>(null)

const props = defineProps<{
    contourParam1: string
    contourParam2: string
    contourObjective: string
}>()

async function render() {
    await nextTick()

    if (!contour.value) 
        return
    if (!experiment_description.value) 
        return
    if (!props.contourParam1 || !props.contourParam2 || props.contourParam1 === "" || props.contourParam2 === "") {
        return
    }
    const result = await MainClientApi.calculatePlot(
        "contour",
        {
            "experiment_description": experiment_description.value,
            "trials": allRes.value,
            "param1": props.contourParam1,
            "param2": props.contourParam2,
            "objective": props.contourObjective
        }
    )

    renderContour(contour.value, result, experiment_description.value)
}

watch(
    [
        allRes, 
        () => props.contourParam1, 
        () => props.contourParam2, 
        () => props.contourObjective
    ],
    () => {
        render()
    },
    { deep: true }
);
</script>



<template>
  <div
    ref="contour"
  ></div>
</template>