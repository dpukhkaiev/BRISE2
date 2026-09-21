<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'

import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model'

//service
import { useMainEventStore } from '../../../../entities/main'

import { useResultTracker, findMatchingPoint } from '../model/result-calc'

// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)


const isChartInitialized = ref(false)

const solution = ref<Solution | null>(null)

const isVisible = ref(false)

const { allRes, bestRes, reset, pushInitial, pushTracked } = useResultTracker()

const impr = ref<HTMLElement | null>(null)

const subs = new Subscription()

onMounted(() => {
    initMainEvents()
})

onUnmounted(() => {
    subs.unsubscribe()
})

async function render() {
    // DOM element. Render point

    const element = impr.value
    const Plotly = store.plotlyInstance
    if (!element || !Plotly) return
    isVisible.value = true
    await nextTick()


    // X-axis data
    const xBest = Array.from(bestRes.value).map((i: any) => i['measured points']);
    // Results
    const yBest = Array.from(bestRes.value).map((i: any) => i['results'][0]);

    const allResultSet = { // Data for all results
        x: Array.from(allRes.value).map((i: any) => i['measured points']),
        y: Array.from(allRes.value).map((i: any) => i['results'][0]),
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: { color: 'rgba(67,67,67,1)', width: 1, shape: 'spline' as const, dash: 'dot' as const },
        text: Array.from(allRes.value).map((i: any) => String(i['configurations'])),
        marker: {
            color: 'rgba(255,64,129,1)',
            size: 8,
            symbol: 'x' as const
        },
        name: 'results'
    };
    const bestPointSet = { // Data for the best available results
        x: xBest,
        y: yBest,
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: { color: 'rgba(67,67,67,1)', width: 2, shape: 'spline' as const },
        name: 'best point',
        marker: { size: 6, symbol: 'x' as const, color: 'rgba(67,67,67,1)' }
    };

    const startEndPoint = { // Start & Finish markers
        x: [xBest[0], xBest[xBest.length - 1]],
        y: [yBest[0], yBest[yBest.length - 1]],
        type: 'scattergl' as const,
        mode: 'markers' as const,
        hoverinfo: 'none' as const,
        showlegend: false,
        marker: { color: 'rgba(255,64,129,1)', size: 10 }
    };

    const finalPoint = solution.value ? findMatchingPoint(solution.value, allRes.value) : null
    const solutionMarker = finalPoint ? {
        x: [finalPoint['measured points']],
        y: [finalPoint.results[0]],
        type: 'scattergl' as const,
        mode: 'markers' as const,
        hoverinfo: 'text' as const,
        text: 'Final solution',
        name: 'Solution',
        marker: { color: 'Gold', size: 16, symbol: 'star' as const, line: { color: 'black', width: 1 } }
    } : null

    const data = solutionMarker
        ? [allResultSet, bestPointSet, startEndPoint, solutionMarker]
        : [allResultSet, bestPointSet, startEndPoint];

    const layout = {
        title: { text: 'Improvement Plot' } as const,
        showlegend: true,
        autosize: true,
        xaxis: {
            title: { text: 'Configuration number' } as const,
            showline: true,
            showgrid: false,
            zeroline: false,
            showticklabels: true,
            linecolor: 'rgb(204,204,204)',
            linewidth: 2,
            autotick: false,
            ticks: 'outside' as const,
            tickcolor: 'rgb(204,204,204)',
            tickwidth: 2,
            ticklen: 5,
            tickfont: {
                family: 'Roboto',
                size: 12,
                color: 'rgb(82, 82, 82)'
            }
        },
        yaxis: {
            title: { text: Object.values(experiment_description.value?.Context?.TaskConfiguration?.Objectives ?? {})[0]?.Name ?? '' } as const,
            showgrid: false,
            zeroline: false,
            showline: true,
            linecolor: 'rgb(204,204,204)',
            showticklabels: true,
            ticks: 'outside' as const,
            tickcolor: 'rgb(204,204,204)',
            ticklen: 5,
            tickfont: {
                family: 'Roboto',
                size: 12,
                color: 'rgb(82, 82, 82)'
            }
        },
    };
    if (element)
        Plotly.react(element, data, layout);
}


function initMainEvents() {
    watch(experiment_description, () => {
        reset()
        solution.value = null
        // pointer to dom element
        const element = impr.value
        isVisible.value = false
        isChartInitialized.value = false
        const Plotly = store.plotlyInstance
        // will clear the div, and remove any Plotly plots that have been placed in it
        if (element && Plotly) {
            Plotly.purge(element)
        }
    }, {
        deep: true,
        immediate: true
    })

    // add start point
    subs.add(store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                pushInitial(configuration)
            })
            // render when chart is initialized
            isVisible.value = true
            nextTick(() => {
                render().then(() => { isChartInitialized.value = true })
            })
            // render() // render chart when all points got
        }
    }))

    // add last point
    subs.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                solution.value = configuration
                if (!findMatchingPoint(configuration, allRes.value)) {
                    pushInitial(configuration)
                }
            });
            isVisible.value = true
            nextTick(() => {
                render()
            })
        }
    }))

    // add new point
    subs.add(store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);

            // check the best availbale point
            const descr = experiment_description.value

            let objectives = descr?.['Context']?.['TaskConfiguration']?.['Objectives'] as any
            if (!objectives) return
            const firstObjectiveKey = Object.keys(objectives)[0]
            console.log('TaskConfig', descr?.['TaskConfiguration'])
            const isMinimization = objectives?.[firstObjectiveKey]?.['Minimization']


            configs.forEach((configuration: any) => {
                pushTracked(configuration, isMinimization)
            })
            isVisible.value = true
            nextTick(() => {
                render()
            })
        }

    }))
}





</script>

<template>
  <div
    v-show="isVisible"
    ref="impr"
  />
</template>