<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'

import { MainEvent } from '../../../../entities/main'

//service
import { useMainEventStore } from '../../../../entities/main'
import { usePlotStore } from '../../../../entities/main/model/plot.store'
import type { PointExp } from '../../../../entities/main/model/plot.store'
import { parseJsonWithInfinity, stringifyWithInfinity } from '../../../../shared/lib'

defineOptions({ name: 'SkeletonChart' })

// initialize store
const store = useMainEventStore()
const plotStore = usePlotStore()
// destructure reactive value from main.event.store
const { experiment_description, experimentFinished } = storeToRefs(store)
const { selected, visibleCharts, allRes, solution } = storeToRefs(plotStore)

const subs = new Subscription()

onMounted(() => {
    initMainEvents()
})

onUnmounted(() => {
    subs.unsubscribe()
})

// an already measured point with the same configuration and results, if any
function findMatchingPoint(configuration: any): PointExp | undefined {
    const configurations = stringifyWithInfinity(configuration.configurations)
    const results = stringifyWithInfinity(configuration.results)
    return allRes.value.find(point =>
        stringifyWithInfinity(point.configurations) === configurations &&
        stringifyWithInfinity(point.results) === results
    )
}

function initMainEvents() {
    watch(experiment_description, () => {
        allRes.value = []
        solution.value = null
        selected.value['Optimization History'] = !!experiment_description.value?.PlotSelection?.Plot?.OptimizationHistory
        selected.value['Parallel Coordinates'] = !!experiment_description.value?.PlotSelection?.Plot?.ParallelCoordinates
        selected.value['Rank Plot'] = !!experiment_description.value?.PlotSelection?.Plot?.RankPlot
        selected.value['Hyperparameter Importances']= !!experiment_description.value?.PlotSelection?.Plot?.HyperparameterImportances
        selected.value['Slice Plot'] = !!experiment_description.value?.PlotSelection?.Plot?.SlicePlot
        selected.value['Contour Plot'] = !!experiment_description.value?.PlotSelection?.Plot?.ContourPlot
        selected.value['Pareto Front'] = !!experiment_description.value?.PlotSelection?.Plot?.ParetoFront
        selected.value['EDF Plot'] = !!experiment_description.value?.PlotSelection?.Plot?.EDFPlot
        selected.value['Heatmap'] = !!experiment_description.value?.PlotSelection?.Plot?.Heatmap
        // disabled, see the HeatmapReg import comment in App.vue
        // selected.value['Heatmap Reg'] = !!experiment_description.value?.PlotSelection?.Plot?.HeatmapReg
        visibleCharts.value = Object.entries(selected.value)
            .filter(([, enabled]) => enabled)
            .map(([name]) => name)
    }, {
        deep: true,
        immediate: true
    })

    // add start point
    subs.add(store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (experimentFinished.value) return
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body)
            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: PointExp = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp)
            })
        }
    }))

    // add last point
    subs.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body);
            configs.forEach((configuration: any) => {
                // the solution is usually one of the measured configurations: don't count it twice
                const measuredPoint = findMatchingPoint(configuration)
                if (measuredPoint) {
                    solution.value = measuredPoint
                    return
                }
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: PointExp = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp);
                solution.value = temp
            });
        }
    }))

    // add new point
    subs.add(store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (experimentFinished.value) return
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body);

            // check the best availbale point
            const descr = experiment_description.value

            let objectives = descr?.['Context']?.['TaskConfiguration']?.['Objectives'] as any
            if (!objectives) return


            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                // number der measuret points before pushing into an array
                const currentPointIndex = allRes.value.length + 1;

                const temp: PointExp = {
                    'configurations': configuration.configurations,
                    'results': configuration.results,
                    'time': min + 'm ' + sec + 's',
                    'measured points': currentPointIndex
                };

                allRes.value.push(temp) // add new point (result)
            })
        }
    }))
}
</script>
<template>
  <!-- Controller component -->
  <div style="display: none;" />
</template>
