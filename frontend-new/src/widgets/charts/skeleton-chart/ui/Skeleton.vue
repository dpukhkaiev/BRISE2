<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'

import { MainEvent } from '../../../../entities/main'

//service
import { useMainEventStore } from '../../../../entities/main'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import type { PointExp } from '../../../../entities/main/model/plot.store'



// initialize store
const store = useMainEventStore()
const plotStore = usePlotStore()
// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)
const { selected, visibleCharts, bestRes, allRes } = storeToRefs(plotStore)

onMounted(() => {
    initMainEvents()
})

function initMainEvents() {
    watch(experiment_description, () => {
        bestRes.value = []
        allRes.value = []
        selected.value.optHist = !!experiment_description.value?.PlotSelection?.Plot?.OptimizationHistory
        selected.value.paraCoord = !!experiment_description.value?.PlotSelection?.Plot?.ParallelCoordinates
        selected.value.rank = !!experiment_description.value?.PlotSelection?.Plot?.RankPlot
        selected.value.hypImp= !!experiment_description.value?.PlotSelection?.Plot?.HyperparameterImportances
        selected.value.slice = !!experiment_description.value?.PlotSelection?.Plot?.SlicePlot
        selected.value.contour = !!experiment_description.value?.PlotSelection?.Plot?.ContourPlot
        selected.value.paretoFront = !!experiment_description.value?.PlotSelection?.Plot?.ParetoFront
        selected.value.edf = !!experiment_description.value?.PlotSelection?.Plot?.EDFPlot
        selected.value.intVal = !!experiment_description.value?.PlotSelection?.Plot?.IntermediateValues
        selected.value.termImpr= !!experiment_description.value?.PlotSelection?.Plot?.TerminatorImprovement
        selected.value.timeline = !!experiment_description.value?.PlotSelection?.Plot?.TimelinePlot
        visibleCharts.value = Object.entries(selected.value)
            .filter(([_, enabled]) => enabled)
            .map(([name]) => name)
        //console.log("hypImp value: ", selected.value.hypImp)
    }, {
        deep: true,
        immediate: true
    })

    // add start point
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: any = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp)
                bestRes.value.push(temp)
            })
        }
    })

    // add last point
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: any = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp);
                bestRes.value.push(temp); // There is no check if this solution is the best decision
            });
        }
    })

    // add new point
    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);

            // check the best availbale point
            const descr = experiment_description.value

            let objectives = descr?.['Context']?.['TaskConfiguration']?.['Objectives'] as any
            if (!objectives) return
            const firstObjectiveKey = Object.keys(objectives)[0]
            const isMinimization = objectives?.[firstObjectiveKey]?.['Minimization']


            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                // number der measuret points before pushing into an array
                const currentPointIndex = allRes.value.length + 1;

                allRes.value.push({
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': currentPointIndex
                }) // add new point (result)

                const temp: PointExp = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': currentPointIndex
                }

                // compare to the last best point
                const lastBest = bestRes.value.at(-1)
                if (lastBest) {
                    const isBetter = isMinimization ? temp.results[0] < lastBest.results[0] : temp.results[0] > lastBest.results[0]
                    if (!isBetter) {
                        temp.results = lastBest.results
                        temp.configurations = lastBest.configurations
                    }
                }

                bestRes.value.push(temp) // add the best availbale point(result)
            })
        }
    })
}
</script>
<template>
  <!-- Controller component -->
  <div style="display: none;"></div>
</template>