<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
//import { useDebounceFn } from '@vueuse/core'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'

import { Color } from '../../model/chart.types'
import { theme } from '../../model/heatmap-theme'

import { MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../../entities/main'
import { cleanIdentifier, parseJsonWithInfinity, stringifyWithInfinity } from '../../../../shared/lib'

import { DataTransformer } from '../../../../entities/experiment/lib/data.transformer'
import { axisValues } from '../../../../entities/experiment/lib/search-space'
import { INACTIVE_LABEL } from '../../../../entities/experiment/lib/inactive'

defineOptions({ name: 'HeatmapChart' })

interface Configuration {
    configurations: Array<any>;
    results: any;
}

// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, regions, searchspaceReady, experimentFinished } = storeToRefs(store)

// experiment results
const result = ref(new Map<string, any>())

// prediction results from model
const prediction = ref(new Map<string, any>())

// best point
let solution: Solution
const configWithNones = ref('')

const measPoints = ref<Array<[any, any]>>([])
let defaultConfiguration: Configuration
let sol: any = ref()
let dc: any = ref()
let results = ref('')

// rendering axises
const x = ref<Array<any>>([])
const y = ref<Array<any>>([])
const xParamKey = ref('')
const yParamKey = ref('')
const xTitle = ref('')
const yTitle = ref('')
const keyParam = ref('')


// values that possible to use in template
const colors = Color


const map = ref<HTMLElement | null>(null)

// the label of a value on an axis; a configuration without the parameter is drawn at the inactive label
function axisLabel(value: string | number | null | undefined): string {
    return value === undefined ? INACTIVE_LABEL : cleanIdentifier(value)
}

// the label of a configuration's value on an axis, which gets an inactive row or column on first need
function labelOnAxis(value: string | number | null | undefined, axis: { value: Array<any> }): string {
    const label = axisLabel(value)
    if (label === INACTIVE_LABEL && !axis.value.includes(INACTIVE_LABEL)) {
        axis.value.push(INACTIVE_LABEL)
    }
    return label
}

// the heatmap has axes only if two parameters are active in every trial
const hasAxes = computed(() => xParamKey.value !== '' && yParamKey.value !== '')

// remembers a measured configuration at its place on the heatmap. Without axes every configuration would sit at
// 'inactive' on both, and Plotly adds a category to an axis for every value it is given.
function recordPoint(configuration: any) {
    if (!hasAxes.value) return
    const conf = configuration['configurations'];
    const yVal = labelOnAxis(conf[yParamKey.value], y);
    const xVal = labelOnAxis(conf[xParamKey.value], x);
    result.value.set(String([yVal, xVal]), configuration['results']);
    measPoints.value.push([yVal, xVal]);
}

const subs = new Subscription()

function resetRes() {
    result.value?.clear()
    prediction.value?.clear()
    measPoints.value = []
}

//
const resultLookup = computed(() => {
    const map = new Map<string, number>()
    result.value.forEach((v, k) => map.set(k, v?.[keyParam.value]))
    return map
})
// const zMatrix = computed(() => DataTransformer.buildZMatrix(
//     x.value.map(String),
//     y.value.map(String),
//     resultLookup.value))

async function render(): Promise<void> {
    const Plotly = store.plotlyInstance

    if (!Plotly) return
    if (!hasAxes.value) {
        // Plotly adds a category to an axis for every value it is given, so there is nothing to draw
        if (map.value) Plotly.purge(map.value)
        return
    }
    const zData = DataTransformer.buildZMatrix(x.value.map(String), y.value.map(String), resultLookup.value)
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
        { // Best point solution
            type: 'scatter' as const,
            mode: 'markers' as const,
            hoverinfo: 'none' as const,
            showlegend: false as const,
            marker: { color: 'Gold', size: 16, symbol: 'star' },
            x: solution && hasAxes.value ? [axisLabel((solution.configurations as any)[xParamKey.value])] : [],
            y: solution && hasAxes.value ? [axisLabel((solution.configurations as any)[yParamKey.value])] : []
        }
    ];

    const layout: any = {
        margin: { l: 220 },
        title: { text: 'Heat map results' } as any,
        autosize: true,
        showlegend: false,
        xaxis: {
            title: { text: xTitle.value },
            type: 'category' as const,
            autorange: true,
            range: [-0.5, x.value.length - 0.5],
            showgrid: true,
            categoryorder: 'array',
            categoryarray: x.value
        },
        yaxis: {
            title: { text: yTitle.value },
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

function initMainEvents() {
    watch([experiment_description, regions, searchspaceReady], () => {
        if (!experiment_description.value || !searchspaceReady.value) {
            return
        }
        resetRes()
        // the heatmap spans the first two parameters of the top-level region, which are active in every trial
        const [yParam, xParam] = regions.value[0]?.Parameters ?? []
        if (yParam && xParam) {
            yParamKey.value = yParam.Name
            xParamKey.value = xParam.Name
            yTitle.value = cleanIdentifier(yParam.Name)
            xTitle.value = cleanIdentifier(xParam.Name)
            y.value = axisValues(yParam).map(cleanIdentifier)
            x.value = axisValues(xParam).map(cleanIdentifier)
        } else {
            // fewer than two parameters are active in every trial: keep no axes of the previous experiment
            yParamKey.value = ''
            xParamKey.value = ''
            yTitle.value = ''
            xTitle.value = ''
            y.value = []
            x.value = []
        }

        const priorities = (experiment_description.value as any)?.Context?.TaskConfiguration?.Objectives
        if (priorities) {
            keyParam.value = Object.keys(priorities)[0]
        }
    }, {
        deep: true,
        immediate: true
    })

    // new configuration results
    subs.add(store.onEvent(MainEvent.NEW)?.subscribe(async (message: any) => {
        if (experimentFinished.value) return
        const configs = parseJsonWithInfinity(message.body)
        let count = 0;
        for (const configuration of configs) {
            if (configuration) {
                recordPoint(configuration);
            }
            count++;
            if (count % 50 === 0 && 'scheduler' in window && typeof scheduler.yield === 'function') {
                await scheduler.yield();
            }
        }
        // collect all configs first, then render
        nextTick(() => render())
    }))

    // The final configuration, suggested by BRISE.

    subs.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body);
            configs.forEach((configuration: any) => {
                if (configuration) {
                    solution = configuration; // In case if only one point solution
                    defaultConfiguration = configuration;
                    configWithNones.value = stringifyWithInfinity(solution.configurations, '\t');
                    configWithNones.value = configWithNones.value.replace(',,', ',None,');
                    results.value = stringifyWithInfinity(solution.results)
                    recordPoint(configuration);
                    sol.value = Object.values(solution.results)
                    dc.value = Object.values(defaultConfiguration.results)

                } else {
                    console.log('Empty solution');
                }
            });
            render();
        }
    }));

    // Default message
    subs.add(store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (experimentFinished.value) return
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body);
            configs.forEach((configuration: any) => {
                if (configuration) {
                    defaultConfiguration = configuration; // In case if only one point default
                    recordPoint(configuration);
                } else {
                    console.log('Empty default');
                }
            });
            console.log('Default:', message.body);
            render();
        }
    }));

}

onMounted(() => {
    initMainEvents()
})

onUnmounted(() => {
    subs.unsubscribe()
})


</script>
<template>
  <div>
    <div
      v-if="searchspaceReady && !hasAxes"
      class="text-body-2 text-medium-emphasis"
      style="margin: 10px"
    >
      Not enough parameters in the top-level region for a heatmap.
    </div>
    <div
      v-show="hasAxes"
      ref="map"
    />
    <select
      v-show="hasAxes"
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
  </div>
</template>