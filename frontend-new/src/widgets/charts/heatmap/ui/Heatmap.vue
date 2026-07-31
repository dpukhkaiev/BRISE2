<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { Color, PlotType, Smooth } from '../../model/chart.types'
import type { Solution } from '../../../../entities/task/model/task-data.model';
import { useMainEventStore } from '../../../../entities/main'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import { renderHeatmap } from '../render'

const store = useMainEventStore()
const { experiment_description, searchspace } = storeToRefs(store)
const plotStore = usePlotStore()
const { allRes } = storeToRefs(plotStore)
const result = ref(new Map<string, any>())
const measPoints = ref<Array<[any, any]>>([])
const solution = ref<Solution>()

const heatmapParam1 = ref("")
const heatmapParam2 = ref("")

const x = ref<Array<any>>([])
const y = ref<Array<any>>([])

const theme = ref({
    type: PlotType[0] as string,
    color: Color[0] as string,
    smooth: Smooth[0] as string | boolean
})

const heatmap = ref<HTMLElement | null>(null)

async function render() {
    await nextTick()

    if (!heatmap.value) return
    if (!experiment_description.value) 
        return
    renderHeatmap(heatmap.value, {
        result: result.value,
        measPoints: measPoints.value,
        solution: solution.value,
        x: x.value,
        y: y.value,
        theme: theme.value,
        xLabel: Object.keys(searchspace.value.boundaries[0].Boundaries)[1],
        yLabel: Object.keys(searchspace.value.boundaries[0].Boundaries)[0]
    })
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
    ref="heatmap"
  ></div>
</template>