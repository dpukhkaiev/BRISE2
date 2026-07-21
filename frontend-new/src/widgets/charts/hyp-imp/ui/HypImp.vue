<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderHypImp } from '../render'
import { storeToRefs } from 'pinia'
import { MainClientApi } from '../../../../entities/main/api/main.client.store'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const hypimp = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!hypimp.value) return
    const result = await MainClientApi.calculatePlot(
        "hyperparameter_importances",
        {
            experiment_description: experiment_description,
            trials: plotStore.allRes
        }
    )

    renderHypImp(hypimp.value, result)
}

watch(
    allRes,
    () => {
        render()
    },
    { deep: true }
)
</script>



<template>
  <div
    ref="hypimp"
  ></div>
</template>