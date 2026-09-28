<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderRank } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

defineOptions({ name: 'RankChart' })

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description, plotlyInstance } = storeToRefs(store)
const rank = ref<HTMLElement | null>(null)

const props = defineProps<{
    rankParam1: string
    rankParam2: string
    rankObjective: string
}>()

async function render() {
    await nextTick()

    if (!plotlyInstance.value) return
    if (!rank.value) 
        return
    if (!experiment_description.value) 
        return
    renderRank(plotlyInstance.value, rank.value, allRes.value, props.rankParam1, props.rankParam2, props.rankObjective, experiment_description.value)
}

watch(
    [
        allRes, 
        () => props.rankParam1, 
        () => props.rankParam2, 
        () => props.rankObjective
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
    if (rank.value && plotlyInstance.value) {
        plotlyInstance.value.purge(rank.value)
    }
})
</script>



<template>
  <div
    ref="rank"
  />
</template>