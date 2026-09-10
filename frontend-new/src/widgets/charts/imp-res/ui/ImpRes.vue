<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'

// Plotly
//import Plotly from 'plotly.js-dist-min'

import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../../entities/main'

import { useResultTracker } from '../model/result-calc'

interface PointExp {
    configurations: Array<any>;
    results: Array<any>;
    time: any;
    'measured points': number;
}
// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)


const isChartInitialized = ref(false)

let solution: Solution

const isVisible = ref(false)

let plotlyInstance: typeof import('plotly.js-dist-min') | null = null

const { allRes, bestRes, reset, pushInitial, pushTracked } = useResultTracker()

const impr = ref<HTMLElement | null>(null)

// lazy loading plotly
async function getPlotly() {
    if (!plotlyInstance) {
        plotlyInstance = await import('plotly.js-dist-min')
    }
    return plotlyInstance
}


onMounted(() => {
    initMainEvents()
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

    const data = [allResultSet, bestPointSet, startEndPoint];

    const layout = {
        title: { text: 'The best results' } as const,
        showlegend: true,
        autosize: true,
        xaxis: {
            title: { text: 'Sequence number' } as const,
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
        // pointer to dom element 
        const element = impr.value
        isVisible.value = false
        isChartInitialized.value = false
        const Plotly = plotlyInstance
        // will clear the div, and remove any Plotly plots that have been placed in it
        if (element && Plotly) {
            Plotly.purge(element)
        }
    }, {
        deep: true,
        immediate: true
    })

    // add start point
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                solution = configuration
                pushInitial(configuration)
            })
            // render when chart is initialized
            isVisible.value = true
            nextTick(() => {
                render().then(() => { isChartInitialized.value = true })
            })
            // render() // render chart when all points got
        }
    })

    // add last point
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                solution = configuration;
                pushInitial(configuration)
            });
            isVisible.value = true
            nextTick(() => {
                render()
            })
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
            console.log('TaskConfig', descr?.['TaskConfiguration'])
            const isMinimization = objectives?.[firstObjectiveKey]?.['Minimization']


            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                // number der measuret points before pushing into an array
                const currentPointIndex = allRes.value.length + 1;

                allRes.value.push({
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
                    'time': min + 'm ' + sec + 's',
                    'measured points': currentPointIndex
                }) // add new point (resut)

                const temp: PointExp = {
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
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
            isVisible.value = true
            nextTick(() => {
                render()
            })
        }

    })
}





</script>

<template>
    <div v-show="isVisible" ref="impr" />
</template>