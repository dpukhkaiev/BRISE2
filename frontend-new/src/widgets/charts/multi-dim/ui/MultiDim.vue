<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'

// Plotly
import Plotly from 'plotly.js-dist-min'


// Constant
import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../../entities/main'


// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, searchspace } = storeToRefs(store)

// experiment configuration
const parameter_names = ref()
const currentDiagram = ref()
let experiment: string = ''
const rootParam = ref<any[]>([])
let resultParamsRange = ref<Map<string, any>>()
let keyParam = ref('')

//best point 
const allPoints = ref<Map<string, any>[]>([])
let defaultPoint: any

let solution: Solution | null = null

function resetRes() {
    allPoints.value = ([])
    solution = null
    defaultPoint = null
}

function isModelType(type: string) {
    const surrogate = experiment_description.value?.ConfigurationSelection?.Predictor?.Model.Surrogate?.Instance
    const surrogateType = surrogate ? Object.keys(surrogate)[0] : undefined
    return surrogateType === type
    //console.log('isModelType:', type, result, experiment_description.value?.Predictor)
    //return result
}



//return an arry of values by key from all directionaries
function unpack(set: any, key: any) {
    let selection: any = []
    set.forEach((point: any) => {  // point is key value store - Map
        selection.push(point.get(key));
    });
    return selection
}
// merge key and values arrays in key
function zip(keys: Array<any>, values: Array<any>) {
    let result = new Map()
    if (keys.length == values.length) {
        keys.forEach((key, i) => result.set(key, values[i]))
    }
    return result
}
async function chose(configuration: any) {
    console.log('experiment:', experiment)
    console.log('configurations:', configuration.configurations)
    currentDiagram.value = experiment
    let index = rootParam.value.indexOf(currentDiagram.value)
    if (index === -1) {
        console.warn('Parameter not found:', currentDiagram.value, 'in', rootParam)
        return
    }
    parameter_names.value = Object.keys(searchspace.value["boundaries"][index]["Boundaries"])
    let rangeValues = Object.values(searchspace.value["boundaries"][index]["Boundaries"])
    resultParamsRange.value = zip(parameter_names.value, rangeValues)
    resultParamsRange.value.set('result', undefined) // range for results is undefined
}

function initMainEvents() {

    watch(experiment_description, () => {
        if (!experiment_description.value || !searchspace.value) {
            return
        }
        resetRes()

        rootParam.value = searchspace.value["root_parameters_list"]
        console.log('rootParam after:', rootParam.value)
        experiment = searchspace.value["name"]
        // ObjectPriorities does not exist on received data, updated new path 
        let priorities = experiment_description.value?.Context?.TaskConfiguration?.Objectives

        if (priorities) {
            keyParam.value = Object.keys(priorities)[0]  // → "energy"
        }
        // console.log('keyParam:', keyParam.value)
        // console.log('Objectives:', priorities)
        //  console.log('exp_descr: ', experiment_description.value)
    },

        // reactive object from store, need deep to track properties of the object
        { deep: true })
    console.log('exp_descr: ', experiment_description.value)
    // Default configuration
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            if (!rootParam.value || !experiment) {
                console.warn('not ready yet - rootParam or experiment not there ')
                return
            }
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    chose(configuration)
                    if (!parameter_names.value) return
                    defaultPoint = configuration
                    let alphas = new Array();;
                    parameter_names.value.forEach((key: any) => {
                        alphas.push(configuration.configurations[key])
                    })
                    let point = zip(parameter_names.value, alphas)
                    point.set('result', configuration.results[keyParam.value])
                    allPoints.value.push(point)
                    render()
                } else {
                    console.log("Empty default")
                }
            })
            console.log('Default:', configs)


        }
    });

    // New task results
    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            if (!rootParam.value.length || !experiment) {
                return
            }
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    chose(configuration)
                    if (!parameter_names.value) return
                    var alphas = new Array();;
                    parameter_names.value.forEach((key: any) => {
                        alphas.push(configuration.configurations[key])
                    })
                    let point = zip(parameter_names.value, alphas)
                    point.set('result', configuration.results[keyParam.value])
                    allPoints.value.push(point)
                    render()
                }
                else {
                    console.log("Empty task")
                }
            })


        }
    });

    // The final configuration, suggested by BRISE.
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    solution = configuration
                    console.log('Final:', configs)
                } else {
                    console.log("Empty solution")
                }
            })
        }
    });
}

function render() {

    const element = document.getElementById(currentDiagram.value)
    if (!element) {
        console.warn('element not found', currentDiagram.value)
        return
    }

    var trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            // reversescale: true,
            colorscale: 'Jet',
            color: unpack(allPoints.value, 'result')
        },
        dimensions: dimmensionsData()
    }];

    var layout = {
        title: {
            text: currentDiagram.value,
            font: {
                size: 20
            },
            xref: 'paper' as const,
            x: 0.05,
        }
    }

    Plotly.react(element, trace, layout)
}

function factoryDimension(parameter: String, valuesRange: Array<any>) {
    let dimValues = unpack(allPoints.value, parameter)
    let dim: any = {
        values: dimValues,
        label: parameter.replace(/_/g, " ")
    }
    // If values are not numerical.
    if (valuesRange && (typeof valuesRange[0] == "string" || typeof valuesRange[0] == "boolean")) {
        dim.tickvals = Array.from(Array(valuesRange.length).keys())
        dim.ticktext = valuesRange
        dim.values = dimValues.map((value: any) => dim.tickvals[dim.ticktext.indexOf(value)])
    }
    return dim
}

function dimmensionsData() {
    let data: any = [] // accommodate dimensional obj
    resultParamsRange.value?.size && resultParamsRange.value.forEach((range: Array<any>, param: String) => {
        if (param != experiment) {
            let dim = factoryDimension(param, range) // make dimensional object through all results by one parameter
            data.push(dim) // add new dimension object for plotting
        }
    })
    return data
}

onMounted(() => {
    initMainEvents()
})
</script>

<template>
    <div v-for="item in rootParam" :key="item">
        <v-card>

            <div :id="item" style="width:100%; height:500px;"></div>
        </v-card>
    </div>
</template>