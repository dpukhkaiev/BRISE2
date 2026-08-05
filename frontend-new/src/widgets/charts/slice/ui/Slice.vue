<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderSlice } from '../render'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from '../../../../entities/main'

const plotStore = usePlotStore()
const store = useMainEventStore()
const { allRes } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)
const slice = ref<HTMLElement | null>(null)

const props = defineProps<{
    sliceParam: string
    sliceObjective: string
}>()

async function render() {
    await nextTick()

    if (!slice.value) return
    if (!experiment_description.value) 
        return
    renderSlice(slice.value, allRes.value, props.sliceParam, props.sliceObjective)
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
    ref="slice"
  ></div>
</template>