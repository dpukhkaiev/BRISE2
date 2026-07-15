<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderHypImp } from '../render'
import { storeToRefs } from 'pinia'

const plotStore = usePlotStore()
const { allRes } = storeToRefs(plotStore)
const hypimp = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!hypimp.value) return

    renderHypImp(hypimp.value)
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