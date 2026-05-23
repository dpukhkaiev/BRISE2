<script setup lang="ts">
import { onMounted, ref, computed, watch, onUnmounted, shallowRef } from 'vue'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'

import { MainEvent } from '../../../entities/main'
import { Task } from '../../../entities/task/model/task-data.model';
//service
import { useMainEventStore } from '../../../entities/main'


const result = shallowRef<Task[]>([])

const update = ref(false)

// subscription object for saving and unmounting subscriptions
const subs = new Subscription()
let stopWatch: () => void = () => { }

// initialize store
const store = useMainEventStore()

// cache average result calculations
const avgResultCache = new Map<string, any[]>()

// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)
function refresh() {
    result.value = []
    update.value = true
    avgResultCache.clear()
}

const filterValue = ref('')

//batching for improving the performance
const pendingTasks: Task[] = []
let intervalId: ReturnType<typeof setInterval>

function cachedAvg(config: Record<string, any>): any[] {
    const key = JSON.stringify(config)
    if (avgResultCache.has(key)) return avgResultCache.get(key)!
    const avg = getAverageResult(config)
    avgResultCache.set(key, avg)
    return avg
}

function applyFilter(value: string) {
    filterValue.value = value.trim().toLocaleLowerCase()
}

const filteredResult = computed(() => {
    if (!filterValue.value) return result.value

    let params = ''
    let results = ''
    return result.value.filter(task => {
        Object.values(task.config).forEach((param: any) => {
            params = params + param
        })

        Object.values(task.meta.result).forEach(result => {
            results = results + String(result)

        });
        const dataStr = task.id +
            params +
            results;
        return dataStr.indexOf(filterValue.value) != -1;
    })

})

// alternative for function sortingDataAccessor() in vue (rendering through data-table)

const headers = [
    { title: 'Task ID', key: 'id' },
    {
        title: 'Configuration',
        key: 'run',
        sortRaw: (a: Task, b: Task) => {
            const valA = Object.values(a.config)[0] as string
            const valB = Object.values(b.config)[0] as string
            return valA < valB ? -1 : 1
        }
    },
    {
        title: 'Result',
        key: 'roundedResults',
        sortRaw: (a: Task, b: Task) => {
            const valA = Number(Object.values(a.meta.result)[0])
            const valB = Number(Object.values(b.meta.result)[0])
            return valA - valB
        }
    }
]


function searchTasks(search: Record<string, any>) {
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

function replaceNones(config: Record<string, any>) {
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

function getAverageResult(search: Record<string, any>) {
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
    subs.add(store.onEvent(MainEvent.NEW)?.subscribe((message) => {
        if (message.headers['message_subtype'] === 'task') {
            var fresh: Task = new Task(JSON.parse(message.body))
            var params_array = Object.values(fresh.config)
            fresh.stub_config = replaceNones(params_array)
            // add a new task if it is not in the this.result
            //  !result.value.includes(fresh, -1) && result.value.push(fresh);
            pendingTasks.push(fresh) // only collect, not render yet
        }
    }));

    stopWatch = watch(experiment_description, () => {

        update.value = false
        refresh()
    },
        // reactive object from store, need deep to tracl properties of the object
        {
            deep: true,
            immediate: true
        })

}

onMounted(() => {
    initMainEvents()

    intervalId = setInterval(() => {
        if (pendingTasks.length === 0) return
        result.value.push(...pendingTasks.splice(0, 20))
    }, 500)

})

onUnmounted(() => {
    clearInterval(intervalId)
    subs.unsubscribe()
    stopWatch()
})
const expanded = ref<string[]>([])
</script>

<template>
    <div class="box" v-if="update">
        <v-card elevation="4">
            <v-card-title>
                <h5>Result <span class="length">({{ result.length }})</span></h5>
            </v-card-title>
            <v-text-field variant="outlined" @keyup="(e: any) => applyFilter(e.target.value)" placeholder="Filter">
            </v-text-field>

            <v-data-table-virtual show-expand v-model:expanded="expanded" class="result" :headers="headers"
                :items="filteredResult">
                <!-- Configuration Column -->
                <template v-slot:item.run="{ item }">
                    <span v-for="(value, key) in item.config" :key="key">
                        {{ key }} = {{ value }} ;
                    </span>
                </template>
                <template v-slot:item.roundedResults="{ item }">
                    <span v-for="(value, key) in item.roundedResults" :key="key">
                        {{ key }} = {{ value }} ;
                    </span>
                </template>


                <!-- Expanded Content Column -->
                <template #expanded-row="{ item }">
                    <div v-memo="[item.id, expanded.includes(item.id)]">

                        <v-chip v-for="(value, key) in item.config" :key="key">
                            {{ key }}: {{ value }}
                        </v-chip>
                    </div>

                    <v-list>
                        <v-list-item>Worker: {{ item.meta.worker }}</v-list-item>
                        <v-list-item>Repetitions {{ searchTasks(item.config).length }}</v-list-item>
                        <v-list-item>
                            Average result:

                            <span v-for="(res, index) in cachedAvg(item.config)" :key="index">
                                {{ res.toFixed(2) }}
                                <span v-if="index < cachedAvg(item.config).length - 1"> ; </span>
                            </span>


                        </v-list-item>
                    </v-list>
                </template>
            </v-data-table-virtual>
        </v-card>
    </div>
</template>