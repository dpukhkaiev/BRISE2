<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'

// constant
import { MainEvent, useMainEventStore } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

import { cleanIdentifier } from '../../../../shared/lib'

import { zip, unpack, dimmensionsData } from '../model/dimension-lib'

// initialize store
const store = useMainEventStore()
const { experiment_description, searchspace } = storeToRefs(store)


const parameter_names = ref<string[]>()
const currentDiagram = ref<string>()
let experiment: string = ''
const rootParam = ref<any[]>([])
let resultParamsRange = ref<Map<string, any>>()
let keyParam = ref('')

// collect all points
const allPoints = ref<Map<string, any>[]>([])
let defaultPoint: any
let solution: Solution | null = null

let renderTimer: ReturnType<typeof setTimeout> | null = null

function resetRes() {
    allPoints.value = []
    solution = null
    defaultPoint = null
}



async function chose() {
    if (!rootParam.value || rootParam.value.length === 0) return

    let index = rootParam.value.indexOf(experiment)
    if (index === -1) {
        index = rootParam.value.findIndex(p => cleanIdentifier(p) === experiment)
    }
    if (index === -1) index = 0 // fallback

    currentDiagram.value = rootParam.value[index]

    const boundariesObj = searchspace.value["boundaries"]?.[index]?.["Boundaries"]
    if (!boundariesObj) return

    parameter_names.value = Object.keys(boundariesObj)
    let rangeValues = Object.values(boundariesObj)
    const shortNames = parameter_names.value.map(cleanIdentifier)

    resultParamsRange.value = zip(shortNames, rangeValues)
    resultParamsRange.value.set('result', undefined)
}
function initMainEvents() {
    watch([experiment_description, searchspace], () => {
        if (!experiment_description.value || !searchspace.value) {
            return
        }
        resetRes()

        rootParam.value = searchspace.value["root_parameters_list"]
        experiment = searchspace.value["name"]

        chose()
        let priorities = experiment_description.value?.Context?.TaskConfiguration?.Objectives

        if (priorities) {
            keyParam.value = Object.keys(priorities)[0]
        }
    },
        {
            deep: true,
            immediate: true
        })

    // Default message
    store.onEvent(MainEvent.DEFAULT)?.subscribe(async (message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            if (!rootParam.value || !experiment) {
                console.warn('not ready yet - rootParam or experiment not there ')
                return
            }
            let configs = JSON.parse(message.body)
            let count = 0;
            for (const configuration of configs) {
                if (configuration) {
                    if (!parameter_names.value) return
                    defaultPoint = configuration
                    let alphas = new Array();
                    parameter_names.value.forEach((key: any) => {
                        const rawVal = configuration.configurations[key]
                        // cleaning the labels 
                        alphas.push(cleanIdentifier(rawVal))
                    })
                    let point = zip(parameter_names.value.map(cleanIdentifier), alphas)
                    point.set('result', configuration.results[keyParam.value])
                    allPoints.value.push(point)
                }

                count++;
                if (count % 50 === 0 && typeof scheduler !== 'undefined' && scheduler.yield) {
                    await scheduler.yield();
                }
            }

            if (renderTimer) clearTimeout(renderTimer)
            renderTimer = setTimeout(async () => {
                if (typeof scheduler !== 'undefined' && scheduler.yield) {
                    await scheduler.yield()
                }
                render()
                renderTimer = null
            }, 500)
        }
    });

    // New points
    store.onEvent(MainEvent.NEW)?.subscribe(async (message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            if (!rootParam.value || !rootParam.value.length || !experiment) {
                return
            }
            let configs = JSON.parse(message.body)
            let count = 0;

            for (const configuration of configs) {
                if (configuration) {
                    if (!parameter_names.value) return
                    var alphas = new Array();
                    parameter_names.value.forEach((key: any) => {
                        const rawVal = configuration.configurations[key]
                        alphas.push(cleanIdentifier(rawVal))
                    })
                    let point = zip(parameter_names.value.map(cleanIdentifier), alphas)
                    point.set('result', configuration.results[keyParam.value])
                    allPoints.value.push(point)
                }

                count++;
                if (count % 50 === 0 && typeof scheduler !== 'undefined' && scheduler.yield) {
                    await scheduler.yield();
                }
            }

            if (renderTimer) clearTimeout(renderTimer)
            renderTimer = setTimeout(async () => {
                if (typeof scheduler !== 'undefined' && scheduler.yield) {
                    await scheduler.yield()
                }
                render()
                renderTimer = null
            }, 500)
        }
    });

    // Final message
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            if (!parameter_names.value) return
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    solution = configuration

                }


            });
        }
    })
}
async function render(): Promise<void> {
    if (!currentDiagram.value) return

    const Plotly = store.plotlyInstance
    const element = document.getElementById(currentDiagram.value)

    if (!Plotly || !element) {
        console.warn('DOM Element noch nicht bereit für ID:', currentDiagram.value)
        return
    }

    const dims = dimmensionsData(resultParamsRange.value, experiment, allPoints.value)
    if (!dims || dims.length === 0) return

    var trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            colorscale: 'Jet',
            color: unpack(allPoints.value, 'result').map((v: any) => Number(v) || 0)
        },
        dimensions: dims
    }];

    var layout = {
        margin: { l: 200, r: 50, b: 50, t: 50 },
        title: {
            text: cleanIdentifier(currentDiagram.value),
            font: { size: 18 }
        }
    }

    Plotly.react(element, trace, layout)
}



onMounted(() => {
    initMainEvents()
})

onUnmounted(() => {
    if (renderTimer) clearTimeout(renderTimer)
    const element = document.getElementById(currentDiagram.value!)
    const Plotly = store.plotlyInstance

    if (element && Plotly) {
        Plotly.purge(element)
    }
})
</script>

<template>
    <div v-for="item in rootParam" :key="item">
        <div :id="item" style="width:100%; height:500px;" />
    </div>
</template>