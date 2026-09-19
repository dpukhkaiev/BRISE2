import { ref } from 'vue'


export interface PointExp {
    configurations: Array<any>
    results: Array<any>
    time: any
    'measured points': number
}

function formatTime(): string {
    const min = new Date().getMinutes()
    const sec = new Date().getSeconds()
    return `${min}m ${sec}s`
}

export function useResultTracker() {
    const allRes = ref<PointExp[]>([])
    const bestRes = ref<PointExp[]>([])

    function reset() {
        allRes.value = []
        bestRes.value = []
    }

    // used for DEFAULT and FINAL messages: always pushed as both all + bes
    function pushInitial(configuration: any) {
        const point: PointExp = {
            configurations: Object.values(configuration.configurations),
            results: Object.values(configuration.results),
            time: formatTime(),
            'measured points': allRes.value.length + 1
        }
        allRes.value.push(point)
        bestRes.value.push(point)
        return point
    }

    // used for NEW messages: compares against last best point
    function pushTracked(configuration: any, isMinimization: boolean) {
        const currentPointIndex = allRes.value.length + 1
        const point: PointExp = {
            configurations: Object.values(configuration.configurations),
            results: Object.values(configuration.results),
            time: formatTime(),
            'measured points': currentPointIndex
        }
        allRes.value.push(point)

        const candidate: PointExp = { ...point }
        const lastBest = bestRes.value.at(-1)
        if (lastBest) {
            const isBetter = isMinimization
                ? candidate.results[0] < lastBest.results[0]
                : candidate.results[0] > lastBest.results[0]
            if (!isBetter) {
                candidate.results = lastBest.results
                candidate.configurations = lastBest.configurations
            }
        }
        bestRes.value.push(candidate)
        return candidate
    }

    return {
        allRes,
        bestRes,
        reset,
        pushInitial,
        pushTracked
    }
}