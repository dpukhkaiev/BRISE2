<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderEdf } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const edf = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!edf.value) return
    if (!experiment_description.value) 
        return
    renderEdf(edf.value, allRes.value)
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
    ref="edf"
  ></div>
</template>