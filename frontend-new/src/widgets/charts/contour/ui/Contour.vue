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

let rendering = false

async function render() {
    await nextTick()

    if (!contour.value) return
    const result = await MainClientApi.calculatePlot(
        "contour",
        {
            "experiment_description": experiment_description.value,
            "trials": allRes.value
        }
    )

    renderContour(contour.value, result)
}

watch(
    allRes,
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
    ref="contour"
  ></div>
</template>