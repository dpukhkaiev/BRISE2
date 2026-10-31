<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderSlice } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'
import { trialsWithParameters } from '../../../../entities/experiment/lib/regions'

defineOptions({ name: 'SliceChart' })

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { specsByName, plotlyInstance } = storeToRefs(store)
const slice = ref<HTMLElement | null>(null)

const props = defineProps<{
    sliceParam: string
    sliceObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!slice.value) return
    const trials = trialsWithParameters(allRes.value, [props.sliceParam])
    renderSlice(plotlyInstance.value, slice.value, trials, props.sliceParam, props.sliceObjective, specsByName.value)
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