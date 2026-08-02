<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderOptHist } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { experiment_description } = storeToRefs(store)
const { allRes } = storeToRefs(plotStore)
const optHist = ref<HTMLElement | null>(null)
const props = defineProps<{
    optHistObjective: string
}>();

async function render() {
    await nextTick()

    if (!optHist.value) return
    if (!experiment_description.value) 
        return
    renderOptHist(optHist.value, allRes.value, experiment_description.value, props.optHistObjective)
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