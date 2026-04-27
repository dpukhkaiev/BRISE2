<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'

// Plotly
import Plotly from 'plotly.js-dist-min'
import { Color, PlotType, Smooth } from '../../model/chart.types'

import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../../entities/main'

interface Configuration {
    configurations: Array<any>;
    results: any;
}

// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, searchspace, globalConfig } = storeToRefs(store)

// experiment results
const result = ref(new Map<string, any>())

// prediction results from model
const prediction = ref(new Map<string, any>())

// best point
let solution: Solution
const configWithNones = ref('')
// Measured points for the Regresion model from worker-service
// is always an array of arrays (a tuple)
const measPoints = ref<Array<[any, any]>>([])
let defaultConfiguration: Configuration
let sol: any = ref()
let dc: any = ref()
let results = ref('')

// rendering axises
const x = ref<Array<any>>([])
const y = ref<Array<any>>([])


// default theme
const theme = ref({
    type: PlotType[0] as string,
    color: Color[0] as string,
    smooth: Smooth[0] as string | boolean
})

// values that possible to use in template
const colors = Color
const types = PlotType
const smoothOpt = Smooth

const map = ref<HTMLElement | null>(null)

function resetRes() {
    result.value?.clear()
    prediction.value?.clear()
    measPoints.value = []
}

const isModelType = computed(() => {
    const model = experiment_description.value?.ConfigurationSelection?.Predictor?.Model

    if (model?.Surrogate?.Instance?.LinearRegression) {
        return 'regression'
    }

    return 'unknown'
})

function zParser(data: Map<String, any>): Array<Array<any>> {
    // Parse the answears in to array of Y rows
    const z: any = []
    x.value &&
        y.value &&
        y.value.forEach((y: any) => { // y - parameter2
            const row: any = [];
            x.value.forEach((x: any) => { // x - parameter1
                const results = data.get(String([y, x])); // To get horizontal orientation - change to [x,y], vertical - [y,x]
                row.push(results && results[0]); // Get the first result from an array or mark it as undefined.

            });
            z.push(row);
        });
    return z;
}


function render(): void {
    console.log('BOUNDARIES RAW:', searchspace.value.boundaries)
    console.log('KEYS:', Object.keys(searchspace.value.boundaries || {}))

    // if (isModelType.value !== 'regression') return
    console.log('y:', y.value, Array.isArray(y.value))
    console.log('x:', x.value, Array.isArray(x.value))
    console.log('map:', map.value)
    console.log('model:', isModelType.value)
    console.log('x:', x.value)
    console.log('y:', y.value)
    console.log('result size:', result.value.size)
    if (isModelType.value === 'regression') {
        const element = map.value
        console.log('Z matrix:', zParser(result.value))
        const z = zParser(result.value)

        console.log('x length:', x.value.length)
        console.log('y length:', y.value.length)
        console.log('z shape:', z.length, z[0]?.length)
        const data: any[] = [
            { // defined X and Y axises with data, type and color
                z: zParser(result.value),
                x: x.value.map(String),
                y: y.value.map(String),
                type: theme.value.type,
                colorscale: theme.value.color,
                zsmooth: theme.value.smooth
            },
            { // Measured points
                type: 'scatter' as const,
                mode: 'markers' as const,
                marker: { color: 'grey', size: 7, symbol: 'cross' },
                x: measPoints.value.map(arr => arr[1]),
                y: measPoints.value.map(arr => arr[0])
            },
            { // Best point. Solution
                type: 'scatter' as const,
                mode: 'markers' as const,
                hoverinfo: 'none' as const,
                showlegend: false as const,
                marker: { color: 'Gold', size: 16, symbol: 'star' },
                x: solution && [solution.configurations[1]],
                y: solution && [solution.configurations[0]]
            }
        ];

        const layout: any = {
            title: { text: 'Heat map results' } as any,
            autosize: true,
            showlegend: false,
            xaxis: {
                title: Object.keys(searchspace.value.boundaries[0].Boundaries)[1],
                type: 'category' as const,
                autorange: true,
                range: [Math.min(...x.value), Math.max(...x.value)],
                showgrid: true
            },
            yaxis: {
                title: Object.keys(searchspace.value.boundaries[0].Boundaries)[0],
                type: 'category' as const,
                autorange: true,
                range: [Math.min(...y.value), Math.max(...y.value)],
                showgrid: true
            }
        };
        if (element)
            Plotly.react(element, data, layout);
    }
}
function initMainEvents() {
    watch(experiment_description, () => {
        if (!experiment_description.value || !searchspace.value || !globalConfig.value) {
            return
        }
        // Log the model type for debugging
        console.log('model types: ', experiment_description.value?.ConfigurationSelection?.Predictor?.Model)

        resetRes()

        const boundaryObj = searchspace.value?.boundaries?.[0]?.Boundaries
        x.value = boundaryObj?.threads ?? []
        y.value = boundaryObj?.frequency ?? []
        console.log('x FIXED:', x.value)
        console.log('y FIXED:', y.value)
    }, { deep: true })

    // new configuration results
    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        const configs = JSON.parse(message.body)
        configs.forEach((configuration: any) => {
            if (configuration) {
                const conf = configuration['configurations'];
                const freq = conf.frequency;
                const threads = conf.threads;
                result.value.set(String([freq, threads]), configuration['results']);
                measPoints.value.push([freq, threads]);
                console.log('New configuration:', configuration);
            } else {
                console.log('Empty configuration');
            }
        });
        nextTick(() => render())
    })

    // The final configuration, suggested by BRISE.

    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                if (configuration) {
                    solution = configuration; // In case if only one point solution
                    defaultConfiguration = configuration;
                    const conf = configuration['configurations'];
                    result.value.set(String([conf.frequency, conf.threads]), configuration['results']);
                    measPoints.value.push([conf.frequency, conf.threads]);
                    sol = Object.values(solution.results)
                    dc = Object.values(defaultConfiguration.results)
                    console.log('Final:', configs);
                } else {
                    console.log('Empty solution');
                }
            });
            render();
        }
    });

    // Default configuration
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body);
            configs.forEach((configuration: any) => {
                if (configuration) {
                    defaultConfiguration = configuration; // In case if only one point default
                    result.value.set(String(configuration['configurations']), configuration['results']);
                    measPoints.value.push(configuration['configurations']);
                } else {
                    console.log('Empty default');
                }
            });
            console.log('Default:', message.body);
            render();
        }
    });

}

onMounted(() => {
    initMainEvents()
})


</script>
<template>

    <div v-if="isModelType === 'regression'">
        <div ref="map"></div>
    </div>
    <select v-model="theme.color" @change="render">
        <option v-for="col in colors" :key="col" :value="col">
            {{ col }}
        </option>
    </select>
</template>