import { ref, computed  } from 'vue'

import { Task } from '../../../entities/task/model/task-data.model'
import { normalizeConfigKeys } from '../../../shared/lib'

export function useTaskMetrics() {
    const result = ref<Task[]>([])
    const filterValue = ref('')
    // cache average result calculations
    const avgResultCache = new Map<string, any[]>()

    function replaceNones(config: any[]) {
        return config.map(param => {
            if (param == '' || param == null) return 'None'
            return param
        })
    }

    function applyFilter(value: string) {
        filterValue.value = value.trim().toLocaleLowerCase()
    }

    const filteredResult = computed(() => {
        if (!filterValue.value) return result.value

        return result.value.filter(task => {
            let params = ''
            let results = ''
            const cleanConfig = normalizeConfigKeys(task.config)
            Object.values(cleanConfig).forEach((param: any) => { params += param })
            Object.values(task.meta.result).forEach(res => { results += String(res) })

            const dataStr = task.id + params + results
            return dataStr.indexOf(filterValue.value) !== -1
        })
    })

    function searchTasks(search: Record<string, any>) {
        let search_without_Nones = replaceNones(search && Object.values(search))
        let select: Array<Task> = []
        if (search && result.value.length) {
            result.value.forEach(task => {
                let paramsValues = replaceNones(task.config && Object.values(task.config))
                let count_diff = 0
                for (let i = 0; i < search_without_Nones.length; ++i) {
                    if (search_without_Nones[i] !== paramsValues[i]) {
                        count_diff += 1
                    }
                }
                if (count_diff === 0) {
                    select.push(task)
                }
            })
        }
        return select
    }

    function getAverageResult(search: Record<string, any>) {
        let select = searchTasks(search)
        if (!select.length) return []
        
        let avg_res: any[] = []
        let sum: any[][] = []
        for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
            sum[i] = []
        }
        select.forEach(task => {
            for (let i = 0; i < Object.values(task.meta.result).length; i++) {
                task.meta && sum[i].push(Number(Object.values(task.meta.result)[i]))
            }
        })
        for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
            avg_res[i] = sum[i].reduce((a, b) => a + b, 0) / sum[i].length
        }
        return avg_res
    }

    function cachedAvg(config: Record<string, any>): any[] {
        const normalizedConfig = normalizeConfigKeys(config)
        const key = JSON.stringify(normalizedConfig)
        if (avgResultCache.has(key)) return avgResultCache.get(key)!
        const avg = getAverageResult(normalizedConfig)
        avgResultCache.set(key, avg)
        return avg
    }

    function clearCache() {
        avgResultCache.clear()
    }

    return {
        result,
        filteredResult,
        applyFilter,
        replaceNones,
        searchTasks,
        cachedAvg,
        clearCache
    }
}