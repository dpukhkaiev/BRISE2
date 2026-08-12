<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderParetoFront } from '../render'
import { storeToRefs } from 'pinia'
import { MainClientApi } from '../../../../entities/main/api/main.client.store'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const paretofront = ref<HTMLElement | null>(null)

const props = defineProps<{
    paretoObjective1: string
    paretoObjective2: string
    onlyShowParetoFront: boolean
}>()

let rendering = false

async function render() {
    await nextTick()

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

    renderParetoFront(paretofront.value, result, props.onlyShowParetoFront)
}

watch(
    [
        allRes, 
        () => props.paretoObjective1, 
        () => props.paretoObjective2
    ],
    async () => {
        if (rendering) return;

        rendering = true;
        try {
            await render();
        } finally {
            rendering = false;
        }
    },
    { deep: true }
);
</script>



<template>
  <div
    ref="paretofront"
  ></div>
</template>