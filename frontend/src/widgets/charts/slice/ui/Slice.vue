<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderSlice } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

defineOptions({ name: 'SliceChart' })

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description, plotlyInstance } = storeToRefs(store)
const slice = ref<HTMLElement | null>(null)

const props = defineProps<{
    sliceParam: string
    sliceObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!slice.value) return
    if (!experiment_description.value) 
        return
    renderSlice(plotlyInstance.value, slice.value, allRes.value, props.sliceParam, props.sliceObjective, experiment_description.value)
}

watch(
    [
        allRes, 
        () => props.sliceParam, 
        () => props.sliceObjective
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
    if (slice.value && plotlyInstance.value) {
        plotlyInstance.value.purge(slice.value)
    }
})
</script>



<template>
  <div
    ref="slice"
  />
</template>