<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderOptHist } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { experiment_description } = storeToRefs(store)
const { allRes, bestRes } = storeToRefs(plotStore)
const optHist = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!optHist.value) return
    if (!experiment_description.value) 
        return
    renderOptHist(optHist.value, allRes.value, bestRes.value, experiment_description.value)
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
    ref="optHist"
  ></div>
</template>