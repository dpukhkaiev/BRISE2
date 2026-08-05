<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderRank } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const rank = ref<HTMLElement | null>(null)

const props = defineProps<{
    rankParam1: string
    rankParam2: string
    rankObjective: string
}>()

async function render() {
    await nextTick()

    if (!rank.value) return
    if (!experiment_description.value) 
        return
    renderRank(rank.value, allRes.value, props.rankParam1, props.rankParam2, props.rankObjective)
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
    ref="rank"
  ></div>
</template>