<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'
import { Color } from '../../model/chart.types'
import { theme } from '../../model/heatmap-theme'
import { useMainEventStore, MainEvent } from '../../../../entities/main'
import type { Solution } from '../../../../entities/task/model/task-data.model'
import { DataTransformer } from '../../../../entities/experiment/lib/data.transformer'
import { axisValues } from '../../../../entities/experiment/lib/search-space'
import { cleanIdentifier, parseJsonWithInfinity } from '../../../../shared/lib'
const store = useMainEventStore()
const { experiment_description, regions, searchspaceReady, experimentFinished } = storeToRefs(store)

const solution = ref<Solution | null>(null)
const result = ref(new Map<string, any>())
const prediction = ref(new Map<string, any>())
const measPoints = ref<Array<[any, any]>>([])


const x = ref<string[]>([])
const y = ref<string[]>([])
const xTitle = ref<string>('X Axis')
const yTitle = ref<string>('Y Axis')
const xParamKey = ref<string>('')
const yParamKey = ref<string>('')
const keyParam = ref<string>('')
const map = ref<HTMLElement | null>(null)

const colors = Color
// const types = PlotType

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
    return model?.Surrogate?.Instance?.LinearRegression ? 'regression' : 'unknown'
})


const zMatrix = computed(() => {
    return DataTransformer.buildZMatrix(x.value, y.value, prediction.value)
})


const optimumPoint = computed(() => {
    if (!solution.value) return null

    const configs = (solution.value as any).configurations
    const rawXVal = configs?.[xParamKey.value]
    const rawYVal = configs?.[yParamKey.value]


    const cleanX = cleanIdentifier(rawXVal)
    const cleanY = cleanIdentifier(rawYVal)


    const xExists = x.value.includes(cleanX)
    const yExists = y.value.includes(cleanY)



    if (!cleanX || !cleanY || !xExists || !yExists) {
        console.warn('Optimum point is out of axis bounds or invalid:', { cleanX, cleanY })
        return null
    }

    return { x: cleanX, y: cleanY }
})

let retryCount = 0
const MAX_RETRIES = 60

const subs = new Subscription()

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

onUnmounted(() => {
    subs.unsubscribe()
    resizeObserver?.disconnect()
    resizeObserver = null
})

function initMainEvents() {
    subs.add(store.onEvent(MainEvent.PREDICTIONS)?.subscribe(async (message: any) => {
        if (experimentFinished.value) return
        console.log('[Heatmap Debug] PREDICTIONS event received', message)
        const preds = parseJsonWithInfinity(message.body)
        for (const item of preds) {
            if (item && item.configurations) {
                const rawXVal = item.configurations[xParamKey.value]
                const rawYVal = item.configurations[yParamKey.value]

                const cleanX = cleanIdentifier(rawXVal)
                const cleanY = cleanIdentifier(rawYVal)

                prediction.value.set(`${cleanY},${cleanX}`, item['results']?.[keyParam.value])
            }
        }

        nextTick(() => render())

    }))


    watch([experiment_description, regions, searchspaceReady], () => {
        if (!experiment_description.value || !searchspaceReady.value) return
        resetRes()

        // the first two parameters of the top-level region, which are active in every trial
        const [xParam, yParam] = regions.value[0]?.Parameters ?? []
        if (xParam && yParam) {
            xParamKey.value = xParam.Name
            yParamKey.value = yParam.Name
            xTitle.value = cleanIdentifier(xParam.Name)
            yTitle.value = cleanIdentifier(yParam.Name)

            x.value = axisValues(xParam).map(item => cleanIdentifier(item))
            y.value = axisValues(yParam).map(item => cleanIdentifier(item))
        } else {
            // fewer than two parameters are active in every trial: keep no axes of the previous experiment
            xParamKey.value = ''
            yParamKey.value = ''
            xTitle.value = ''
            yTitle.value = ''
            x.value = []
            y.value = []
        }

        const priorities = (experiment_description.value as any)?.Context?.TaskConfiguration?.Objectives
        if (priorities) {
            keyParam.value = Object.keys(priorities)[0]
        }
    }, { deep: true, immediate: true })

    watch([result, prediction, measPoints, solution], () => nextTick(() => render()), { deep: true })


    subs.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            const configs = parseJsonWithInfinity(message.body)
            const res = configs?.[0]
            if (res) {

                solution.value = res
                measPoints.value.push(res['configurations'])
            }
            if (prediction.value.size > 0) {
                nextTick(() => render())
            }
        }
    }))
}
</script>

<template>
  <div v-if="isModelType === 'regression'">
    <div
      ref="map"
      class="heatmap-container"
    />
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
  </div>
</template>

<style scoped>
.heatmap-container {
    min-height: 500px;
    width: 100%;
}
</style>