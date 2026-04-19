<script lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'

import { MainEvent } from '../../../entities/main'
import type { Task } from '../../../entities/task/model/task-data.model';
//service
import { useMainEventStore } from '../../../entities/main'


const result = ref<Task[]>([])
const displayedColumns: String[] = ['id', 'run', 'result'];
const update = ref(false)
const searchSpaceDescription = ref()
// reactive var for expanding a row in a table
const focus = ref([])
const resultData = ref([])
// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
//const { experiment_description, searchspace } = storeToRefs(store)
function refresh() {
    result.value = []
    resultData.value = ([])
    update.value = true
}
function clearFocus(): void {
    focus.value = []
}



function searchTasks(search: Array<any>) {
    let search_without_Nones = replaceNones(search && Object.values(search))
    let select: Array<Task> = []
    if (arguments.length && result.value.length) {
        result.value.map(task => {
            let paramsValues = replaceNones(task.config && Object.values(task.config))
            let count_diff = 0
            for (let i = 0; i < search_without_Nones.length; ++i) {
                if (search_without_Nones[i] != paramsValues[i]) {
                    count_diff = count_diff + 1
                }
            }
            if (count_diff == 0) {
                select.push(task)
            }
        })
    }
    return select
}

function replaceNones(config: Array<any>) {
    let res_config = new Array<any>()
    Array.prototype.forEach.call(config, param => {
        if (param == '' || param == null) {
            res_config.push('None')
        }
        else {
            res_config.push(param)
        }
    });
    return res_config
}

function getAverageResult(search: Array<any>) {
    let select = searchTasks(search)
    let avg_res: any[] = new Array<any>()
    let sum = new Array<Array<any>>()
    for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
        sum[i] = new Array<any>();
    }
    select && select.map(task => {
        for (let i = 0; i < Object.values(task.meta.result).length; i++) {
            task.meta && sum[i].push(Number(Object.values(task.meta.result)[i]))
        }
    })
    for (let i = 0; i < Object.values(select[0].meta.result).length; i++) {
        avg_res[i] = sum[i].reduce((a, b) => a + b, 0) / sum[i].length
    }
    return avg_res
}

function initMainEvents(): void {

}

onMounted(() => {
    initMainEvents()
})
</script>

<template>
    <v-table></v-table>
</template>