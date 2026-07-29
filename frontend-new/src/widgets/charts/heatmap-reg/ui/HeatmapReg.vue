<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { Color, PlotType, Smooth } from '../../model/chart.types'
import { useMainEventStore, MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model'
import { HeatmapDataTransformer } from '../../../../entities/experiment/lib/heatmap-data.transformer'

const store = useMainEventStore()
const { experiment_description, searchspace, globalConfig } = storeToRefs(store)

const solution = ref<Solution | null>(null)
const result = ref(new Map<string, any>())
const prediction = ref(new Map<string, any>())
const measPoints = ref<Array<[any, any]>>([])

// Reaktive Achsen & Titel
const x = ref<string[]>([])
const y = ref<string[]>([])
const xTitle = ref<string>('X Axis')
const yTitle = ref<string>('Y Axis')
const xParamKey = ref<string>('')
const yParamKey = ref<string>('')
const map = ref<HTMLElement | null>(null)

const theme = ref({
    type: PlotType[0] as string,
    color: Color[0] as string,
    smooth: Smooth[0] as string | boolean
})
const colors = Color
const types = PlotType

function resetRes() {
    result.value.clear()
    prediction.value.clear()
    measPoints.value = []
    solution.value = null
}

const isModelType = computed(() => {
    if (!experiment_description.value) return 'unknown'
    const exp = experiment_description.value as any
    const model = exp.ConfigurationSelection?.Predictor?.Model
    return !!model?.Surrogate?.Instance?.LinearRegression ? 'regression' : 'unknown'
})


const zMatrix = computed(() => {
    return HeatmapDataTransformer.buildZMatrix(x.value, y.value, prediction.value)
})


const optimumPoint = computed(() => {
    if (!solution.value) return null

    const configs = (solution.value as any).configurations
    const rawXVal = configs?.[xParamKey.value]
    const rawYVal = configs?.[yParamKey.value]


    const cleanX = HeatmapDataTransformer.cleanIdentifier(rawXVal)
    const cleanY = HeatmapDataTransformer.cleanIdentifier(rawYVal)


    const xExists = x.value.includes(cleanX)
    const yExists = y.value.includes(cleanY)

    console.group('[Heatmap Debug] Optimum Evaluation');
    console.log('Raw Solution:', solution.value);

    console.log('Cleaned:', { cleanX, cleanY });
    console.log('Current X Axis Array:', x.value, '-> Matches?', xExists);
    console.log('Current Y Axis Array:', y.value, '-> Matches?', yExists);
    console.groupEnd();

    if (!cleanX || !cleanY || !xExists || !yExists) {
        console.warn('Optimum point is out of axis bounds or invalid:', { cleanX, cleanY })
        return null
    }

    return { x: cleanX, y: cleanY }
})

let retryCount = 0
const MAX_RETRIES = 60

async function render(): Promise<void> {
    const Plotly = store.plotlyInstance
    if (!Plotly || isModelType.value !== 'regression' || !map.value) return
    if (prediction.value.size === 0 && !solution.value) return


    if (map.value.clientHeight === 0 || map.value.clientWidth === 0) {
        retryLayout()
        return
    }

    retryCount = 0
    // layer 1: heatmap
    const data: any[] = [
        {
            z: zMatrix.value,
            x: x.value,
            y: y.value,
            type: theme.value.type,
            colorscale: theme.value.color,
            zsmooth: theme.value.smooth
        }
    ]

    // layer 2: find optimum
    if (optimumPoint.value) {
        data.push({
            type: 'scatter',
            mode: 'markers',
            name: 'Optimum',
            hoverinfo: 'text',
            hovertext: `Optimum:<br>${xTitle.value}: ${optimumPoint.value.x}<br>${yTitle.value}: ${optimumPoint.value.y}`,
            marker: { color: 'Gold', size: 18, symbol: 'star', line: { color: 'black', width: 1.5 } },
            x: [optimumPoint.value.x],
            y: [optimumPoint.value.y],
            cliponaxis: false
        })
    }

    const layout: any = {
        margin: { l: 70, r: 40, t: 50, b: 80 },
        title: { text: 'Surrogate Model Surface (Regression)' },
        autosize: true,
        showlegend: false,
        xaxis: {
            title: { text: xTitle.value },
            type: 'category',
            categoryorder: 'array',
            categoryarray: x.value,

            range: [-0.5, x.value.length - 0.5],
            automargin: true
        },
        yaxis: {
            title: { text: yTitle.value },
            type: 'category',
            categoryorder: 'array',
            categoryarray: y.value,
            range: [-0.5, y.value.length - 0.5],
            automargin: true
        }
    }

    console.log('[Heatmap-Reg] RENDER STATE', {
        x: x.value,
        y: y.value,
        xTitle: xTitle.value,
        yTitle: yTitle.value,
        predictionSize: prediction.value.size,
        hasSolution: !!solution.value,
        optimum: optimumPoint.value
    })
    console.log('map size:', map.value?.clientWidth, map.value?.clientHeight)
    await Plotly.react(map.value, data, layout, { responsive: true })
}

function retryLayout() {
    if (retryCount++ < MAX_RETRIES) {
        requestAnimationFrame(() => render())
    } else {
        console.error('[Heatmap-Reg] Container never got layout, giving up')
        retryCount = 0
    }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
    initMainEvents()
    resizeObserver = new ResizeObserver(() => {
        if (map.value && map.value.clientHeight > 0) render()
    })
    if (map.value) resizeObserver.observe(map.value)
}
)


function initMainEvents() {
    store.onEvent(MainEvent.PREDICTIONS)?.subscribe(async (message: any) => {
        console.log('[Heatmap Debug] PREDICTIONS event received', message)
        const preds = JSON.parse(message.body)
        for (const item of preds) {
            if (item && item.configurations) {
                const rawXVal = item.configurations[xParamKey.value]
                const rawYVal = item.configurations[yParamKey.value]

                const cleanX = HeatmapDataTransformer.cleanIdentifier(rawXVal)
                const cleanY = HeatmapDataTransformer.cleanIdentifier(rawYVal)

                prediction.value.set(`${cleanY},${cleanX}`, item['results'])
            }
        }

        nextTick(() => render())

    })


    watch([experiment_description, searchspace], () => {
        console.log('[Heatmap-Reg] searchspace RAW', JSON.stringify(searchspace.value))
        if (!experiment_description.value || !searchspace.value || !globalConfig.value) return
        resetRes()

        const boundaryObj = searchspace.value?.boundaries?.[0]?.Boundaries
        console.log('[Heatmap-Reg] boundaryObj FULL', JSON.stringify(boundaryObj, null, 2))
        console.log('[Heatmap-Reg] boundaryObj KEYS', Object.keys(boundaryObj ?? {}))
        if (!boundaryObj) return

        const keys = Object.keys(boundaryObj).filter(k => k !== 'root')
        if (keys.length >= 2) {
            xParamKey.value = keys[0]   // z.B. "frequency" ODER "mutation_type" ODER was auch immer
            yParamKey.value = keys[1]
            xTitle.value = HeatmapDataTransformer.cleanIdentifier(keys[0])
            yTitle.value = HeatmapDataTransformer.cleanIdentifier(keys[1])


            const rawX = boundaryObj[keys[0]] ?? []
            const rawY = boundaryObj[keys[1]] ?? []


            y.value = rawY.map((item: any) => HeatmapDataTransformer.cleanIdentifier(item))
            x.value = rawX.map((item: any) => HeatmapDataTransformer.cleanIdentifier(item))
        }
    }, { deep: true, immediate: true })

    watch([result, prediction, measPoints, solution], () => nextTick(() => render()), { deep: true })


    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        console.log('[Heatmap Debug] Received FINAL event:', message);
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = JSON.parse(message.body)
            const res = configs?.[0]
            if (res) {

                solution.value = res
                measPoints.value.push(res['configurations'])
            }
            if (prediction.value.size > 0) {
                nextTick(() => render())
            }
        }
    })
}
</script>

<template>
    <div v-if="isModelType === 'regression'">
        <div ref="map" class="heatmap-container" />
    </div>
    <select v-model="theme.color" @change="render">
        <option v-for="col in colors" :key="col" :value="col"></option>
    </select>
</template>

<style scoped>
.heatmap-container {
    min-height: 500px;
    width: 100%;
}
</style>