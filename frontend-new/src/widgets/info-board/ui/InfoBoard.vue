<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
// Constant
import { MainEvent } from '../../../entities/main'
import type { Solution } from '../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../entities/main'

interface NewsPoint {
    'time': any;
    'message': string;
}

// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, searchspace } = storeToRefs(store)

// information log
const news = ref<NewsPoint[]>([])

const solution = ref<Solution>()
const configWithNones = ref('')
const result = ref('')
let default_configuration: any
let sol: any
let dc: any

function refresh() {
    solution.value = undefined
    news.value = ([])
}

function initMainEvents(): void {
    // Main events
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            default_configuration = obj[0]
            let temp: NewsPoint = { 'time': Date.now(), 'message': 'Default configuration results received' }
            news.value.push(temp)
            // snackbar.open(temp['message'], '×', {
            //   duration: 3000
            // });
        }
    });

    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            solution.value = obj[0];
            configWithNones.value = JSON.stringify(solution.value?.configurations, null, '\t')
            result.value = JSON.stringify(solution.value?.results)
            sol = Object.values(solution.value?.results || {})
            dc = Object.values(default_configuration.results)
            configWithNones.value = configWithNones.value.replace(",,", ",None,")
            // NewsPOint type everywhere?
            let temp: NewsPoint = {
                'time': Date.now(),
                'message': '★★★ The optimum result is found. The best point is reached ★★★'
            }

            news.value.push(temp)
        }
    });

    // For information messages
    store.onEvent(MainEvent.LOG)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'info' || message.headers['message_subtype'] === 'error') {
            let obj = JSON.parse(message.body)
            let temp = { 'time': Date.now(), 'message': obj }
            news.value.push(temp)
        }
    });


    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    let temp = {
                        'time': Date.now(),
                        'message': 'New results for ' + JSON.stringify(configuration["configurations"], null, '\t')
                    }
                    news.value.push(temp)
                } else {
                    console.log("Empty configuration")
                }
            })
        }
    });

    store.onEvent(MainEvent.PREDICTIONS)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            let temp = {
                'time': Date.now(),
                'message': 'Prediction obtained. ' + obj.length + ' predictions'
            }

            news.value.push(temp)
        }
    });
}

onMounted(() => {
    initMainEvents()
})

</script>

<template>
    <v-expansion-panels>
        <!-- Panel 1 -->
        <v-expansion-panel :disabled="news.length === 0">
            <v-expansion-panel-title class="info">
                Info messages
            </v-expansion-panel-title>
            <v-expansion-panel-text>

            </v-expansion-panel-text>
        </v-expansion-panel>
    </v-expansion-panels>
</template>