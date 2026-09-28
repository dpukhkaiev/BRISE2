<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderEdf } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

defineOptions({ name: 'EdfChart' })

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description, plotlyInstance } = storeToRefs(store)
const edf = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!edf.value) return
    if (!experiment_description.value) 
        return
    renderEdf(plotlyInstance.value, edf.value, allRes.value)
}

watch(
    allRes,
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
    if (edf.value && plotlyInstance.value) {
        plotlyInstance.value.purge(edf.value)
    }
})
</script>



<template>
  <div
    ref="edf"
  />
</template>