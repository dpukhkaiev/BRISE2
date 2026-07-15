<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
//import { useDebounceFn } from '@vueuse/core'
import { storeToRefs } from 'pinia'

// Plotly
//import Plotly from 'plotly.js-dist-min'
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

async function zParser(data: Map<String, any>): Promise<Array<Array<any>>> {
    // Parse the answears in to array of Y rows
    const z: any = []
    for (const yVal of y.value) {
        const row: any = [];
        for (const xVal of x.value) {
            const results = data.get(String([yVal, xVal])); // To get horizontal orientation - change to [x,y], vertical - [y,x]
            row.push(results && results[0]); // Get the first result from an array or mark it as undefined.
        }
        z.push(row);
        // breaking a long task in a lot of short ones
        if ('scheduler' in window && typeof scheduler.yield === 'function') {
            await scheduler.yield();
        }

    }

    return z;
}


async function render(): Promise<void> {
    const Plotly = store.plotlyInstance

    if (!Plotly) return
    if (isModelType.value === 'regression') {
        const zData = await zParser(result.value);
        const element = map.value
        const data: any[] = [
            { // defined X and Y axises with data, type and color
                z: zData,
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
            margin: { l: 220 },
            title: { text: 'Heat map results' } as any,
            autosize: true,
            showlegend: false,
            xaxis: {
                title: Object.keys(searchspace.value.boundaries[0].Boundaries)[1],
                type: 'category' as const,
                autorange: true,
                range: [-0.5, x.value.length - 0.5],
                showgrid: true,
                categoryorder: 'array',
                categoryarray: x.value
            },
            yaxis: {
                title: Object.keys(searchspace.value.boundaries[0].Boundaries)[0],
                type: 'category' as const,
                autorange: true,
                range: [-0.5, y.value.length - 0.5],
                showgrid: true,
                categoryorder: 'array',
                categoryarray: y.value
            }
        };
        if (element)
            Plotly.react(element, data, layout);
    }
}

const lastName = (s: string) => String(s).split('.').pop() ?? String(s)
function initMainEvents() {
    watch(experiment_description, () => {
        if (!experiment_description.value || !searchspace.value || !globalConfig.value) {
            return
        }
        resetRes()
        const boundaryObj = searchspace.value?.boundaries?.[0]?.Boundaries
        x.value = (boundaryObj?.threads ?? []).map(lastName)
        y.value = (boundaryObj?.frequency ?? []).map(lastName)
    }, {
        deep: true,
        immediate: true
    })

    // new configuration results
    store.onEvent(MainEvent.NEW)?.subscribe(async (message: any) => {
        const configs = JSON.parse(message.body)
        let count = 0;
        for (const configuration of configs) {
            if (configuration) {
                const conf = configuration['configurations'];
                const freq = lastName(conf.frequency);
                const threads = lastName(conf.threads);
                result.value.set(String([freq, threads]), configuration['results']);
                measPoints.value.push([freq, threads]);
            }
            count++;
            if (count % 50 === 0 && 'scheduler' in window && typeof scheduler.yield === 'function') {
                await scheduler.yield();
            }
        }
        // collect all configs first, then render once after Vue's DOM update
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
                    configWithNones.value = JSON.stringify(solution.configurations, null, '\t');
                    configWithNones.value = configWithNones.value.replace(',,', ',None,');
                    results.value = JSON.stringify(solution.results)
                    const conf = configuration['configurations'];
                    result.value.set(String([lastName(conf.frequency), lastName(conf.threads)]), configuration['results']);
                    measPoints.value.push([lastName(conf.frequency), lastName(conf.threads)]);
                    sol.value = Object.values(solution.results)
                    dc.value = Object.values(defaultConfiguration.results)

                } else {
                    //console.log('Empty solution');
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
    <div ref="map" />
  </div>
  <select
    v-model="theme.color"
    @change="render"
  >
    <option
      v-for="col in colors"
      :key="col"
      :value="col"
    >
      {{ col }}
    </option>
  </select>
  <select
    v-model="theme.type"
    @change="render"
  >
    <option
      v-for="type in types"
      :key="type"
      :value="type"
    >
      {{ type }}
    </option>
  </select>
</template>