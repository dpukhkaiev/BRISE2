<script setup lang="ts">
import { onMounted, ref, computed, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Subscription } from 'rxjs'

import { MainEvent } from '../../../entities/main'
import { Task } from '../../../entities/task/model/task-data.model';
//service
import { useMainEventStore } from '../../../entities/main'
import { cleanIdentifier, normalizeConfigKeys } from '../../../shared/lib'

import { useTaskMetrics } from '../model/task-metrics'


// extract logic from the model layer
const {
    result,
    filteredResult,
    applyFilter,
    replaceNones,
    searchTasks,
    cachedAvg,
    clearCache
} = useTaskMetrics()

const update = ref(false)

// subscription object for saving and unmounting subscriptions
const subs = new Subscription()
let stopWatch: () => void = () => { }

// initialize store
const store = useMainEventStore()



// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)
function refresh() {
    result.value = []
    update.value = true
    clearCache()
    pendingTasks.length = 0
}


//batching for improving the performance
const pendingTasks: Task[] = []
let intervalId: ReturnType<typeof setInterval>



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

        refresh()
    },
        // reactive object from store, need deep to track properties of the object
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


defineExpose({
    replaceNones,
    result,
    pendingTasks
})
</script>

<template>
    <div v-if="update" class="box">
        <v-card elevation="4">
            <v-card-title>
                <h5>Result <span class="length">({{ result.length }})</span></h5>
            </v-card-title>
            <!--search bar-->
            <v-text-field variant="outlined" placeholder="Filter" @keyup="(e: any) => applyFilter(e.target.value)" />

            <v-data-table-virtual v-model:expanded="expanded" show-expand class="result" :headers="headers"
                :items="filteredResult">
                <!-- Configuration Column -->
                <template #item.run="{ item }">
                    <span v-for="(value, key) in item.config" :key="key">
                        {{ cleanIdentifier(key) }} = {{ cleanIdentifier(value) }} ;
                    </span>
                </template>
                <template #item.roundedResults="{ item }">
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