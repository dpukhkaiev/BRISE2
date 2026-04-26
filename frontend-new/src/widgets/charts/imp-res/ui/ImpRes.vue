<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'

// Plotly
import Plotly from 'plotly.js-dist-min'

import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../../entities/main'

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
const parameter_names = ref()
const currentDiagram = ref()
let experiment: string = ''
const rootParam = ref<any[]>([])
let resultParamsRange = ref<Map<string, any>>()
let keyParam = ref('')
let solution: Solution

const isVisible = ref(false)

//best point 
const bestRes = ref<PointExp[]>([])
// experiment results
const allRes = ref<PointExp[]>([])
let defaultPoint: any
const impr = ref<HTMLElement | null>(null)

onMounted(() => {
    initMainEvents()
})

function initMainEvents() {
    watch(experiment_description, () => {
        bestRes.value = []
        allRes.value = []
        // pointer to dom element 
        const element = impr.value
        isVisible.value = false
        if (element)
            Plotly.purge(element)
    })

    // add start point
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                solution = configuration
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: any = {
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp)
                bestRes.value.push(temp)
            })
            render() // render chart when all points got
        }
    })

    // add last point
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                solution = configuration;
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                const temp: any = {
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                };
                allRes.value.push(temp);
                bestRes.value.push(temp); // There is no check if this solution is the best decision
            });
        }
        render(); // Render chart when all points got
    })

    // add new point
    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                const min = new Date().getMinutes();
                const sec = new Date().getSeconds();
                allRes.value.push({
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length + 1
                }) // add new point (resut)

                const temp: PointExp = {
                    'configurations': Object.values(configuration.configurations),
                    'results': Object.values(configuration.results),
                    'time': min + 'm ' + sec + 's',
                    'measured points': allRes.value.length
                }

                // check the best availbale point
                const descr = experiment_description.value
                bestRes.value && bestRes.value.forEach(function (resItem) {
                    let objectives = descr?.['Context']?.['TaskConfiguration']?.['Objectives'] as any
                    if (!objectives) return
                    const firstObjectiveKey = Object.keys(objectives)[0]
                    console.log('TaskConfig', descr?.['TaskConfiguration'])
                    const isMinimization = objectives?.[firstObjectiveKey]?.['Minimization']
                    if (isMinimization === true) {
                        if (temp.results[0] > resItem.results[0]) { // check FIRST result from array!
                            temp.results = resItem.results;
                            temp.configurations = resItem.configurations;
                        } else {
                            if (temp.results[0] < resItem.results[0]) { // check FIRST result from array!
                                temp.results = resItem.results;
                                temp.configurations = resItem.configurations;
                            }
                        }

                    }
                    bestRes.value.push(temp) // add the best availbale point(result)      

                })
                bestRes.value.length > 2 && render()
            })
        }

    })
}



function render() {
    // DOM element. Render point

    const element = impr.value

    isVisible.value = true
    // X-axis data
    const xBest = Array.from(bestRes.value).map((i: any) => i['measured points']);
    // Results
    const yBest = Array.from(bestRes.value).map((i: any) => i['results'][0]);

    const allResultSet = { // Data for all results
        x: Array.from(allRes.value).map((i: any) => i['measured points']),
        y: Array.from(allRes.value).map((i: any) => i['results'][0]),
        type: 'scatter' as const,
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
        type: 'scatter' as const,
        mode: 'lines+markers' as const,
        line: { color: 'rgba(67,67,67,1)', width: 2, shape: 'spline' as const },
        name: 'best point',
        marker: { size: 6, symbol: 'x' as const, color: 'rgba(67,67,67,1)' }
    };

    const startEndPoint = { // Start & Finish markers
        x: [xBest[0], xBest[xBest.length - 1]],
        y: [yBest[0], yBest[yBest.length - 1]],
        type: 'scatter' as const,
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
            title: { text: experiment_description.value?.['TaskConfiguration']?.['Objectives'][0] } as const,
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

</script>

<template>
    <div v-show="isVisible" ref="impr"></div>
</template>