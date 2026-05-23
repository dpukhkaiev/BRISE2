<script setup lang="ts">
import { onMounted, ref, watch, shallowRef, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
// Constant
import { MainEvent } from '../../../entities/main'
import type { Solution } from '../../../entities/task/model/task-data.model';

//service
import { useMainEventStore } from '../../../entities/main'

import { Subscription } from 'rxjs'

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

// new: shallowRef to imporve performance, 1 shallowRef, 1 render
const solutionState = shallowRef<{
    solution: Solution | undefined,
    configWithNones: string,
    result: string
}>({ solution: undefined, configWithNones: '', result: '' })


let default_configuration: any
let sol: any
let dc: any

const duration = 3000
const snackbar = ref(false)
const snackbarMsg = ref('')

const subscriptions = new Subscription()

let stopWatch: () => void = () => { }

function refresh(): void {
    solutionState.value = {
        solution: undefined,
        configWithNones: '',
        result: ''
    }
    news.value = []
}

// threshold for event news messages
function pushNews(message: string): void {
    const updated = [...news.value, { time: Date.now(), message }]
    news.value = updated.length > 30 ? updated.slice(-30) : updated
}

function initMainEvents(): void {
    // Main events
    subscriptions.add(store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            default_configuration = obj[0]
            let temp = { 'time': Date.now(), 'message': 'Default configuration results received' }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            //SpushNews(temp.message)
            // snackbar.open(temp['message'], '×', {
            //   duration: 3000
            // });
        }

    })
    );

    subscriptions.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            const s = obj[0]
            let config = JSON.stringify(s?.configurations, null, '\t')
            config = config.replace(",,", ",None,")

            if (!default_configuration) {
                console.warn('default_configuration not set yet')
                dc = []
            } else {
                dc = Object.values(default_configuration.results)
            }
            config = config.replace(",,", ",None,")
            solutionState.value = {
                solution: s,
                configWithNones: config,
                result: JSON.stringify(s?.results)
            }
            // NewsPoint type everywhere?
            let temp = {
                'time': Date.now(),
                'message': '★★★ The optimum result is found. The best point is reached ★★★'
            }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            pushNews(temp.message)

        }
    })
    );

    // For information messages
    subscriptions.add(store.onEvent(MainEvent.LOG)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'info' || message.headers['message_subtype'] === 'error') {
            let obj = JSON.parse(message.body)
            let temp = { 'time': Date.now(), 'message': obj }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            pushNews(temp.message)
        }
    })
    );

    // oldValue, newValue?
    stopWatch = watch(experiment_description, () => {
        console.log('experiment_description:', JSON.stringify(experiment_description.value, null, 2))
        refresh()
        /* if (searchspace.value && searchspace.value['size']) {
             searchspace.value['size'] = parseFloat(searchspace.value['size'])
         }*/
        let temp = {
            'time': Date.now(),
            'message': 'The main configurations of the experiment are obtained. Let\'s go! '
        }
        snackbarMsg.value = temp['message']
        pushNews(temp.message)
    },
        // reactive object from store, need deep to tracl properties of the object
        { deep: true })

    subscriptions.add(store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let configs = JSON.parse(message.body)
            configs.forEach((configuration: any) => {
                if (configuration) {
                    let temp = {
                        'time': Date.now(),
                        'message': 'New results for ' + JSON.stringify(configuration["configurations"], null, '\t')
                    }
                    snackbarMsg.value = temp['message']
                    snackbar.value = true
                    pushNews(temp.message)
                } else {
                    console.log("Empty configuration")
                }
            })
        }
    })
    );

    subscriptions.add(store.onEvent(MainEvent.PREDICTIONS)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            let temp = {
                'time': Date.now(),
                'message': 'Prediction obtained. ' + obj.length + ' predictions'
            }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            pushNews(temp.message)
        }
    })
    );
}

onMounted(() => {
    initMainEvents()
})

onUnmounted(() => {
    subscriptions.unsubscribe()
    stopWatch()
})

// decimalPipe alternative
function formatPercent(value: number): string {
    return value.toFixed(2)
}

</script>

<template>
    <v-expansion-panels elevation="2" multiple>
        <!-- Panel 1 -->
        <v-expansion-panel :disabled="news.length === 0">
            <v-expansion-panel-title class="info">
                Info messages

                <v-icon icon="mdi-text-box" class="mx-2"></v-icon>
                <p class="ml-4"> Basic information from the workflow of experiments ({{ news ? news.length : "0" }})
                </p>
            </v-expansion-panel-title>
            <v-expansion-panel-text>


                <!-- Logs list -->

                <v-list lines="two" v-if="news.length != 0">
                    <v-list-item v-for="info in news" :key="info.time" prepend-icon="mdi-check">
                        <v-list-item-title>{{ info.message }}</v-list-item-title>
                        <v-list-item-subtitle>
                            {{ new Date(info.time).toLocaleDateString() }}
                        </v-list-item-subtitle>
                        <v-divider />
                    </v-list-item>
                </v-list>
            </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Panel 2 -->
        <v-expansion-panel :disabled="!solutionState.solution">
            <v-expansion-panel-title>
                Solution

                <v-icon icon="mdi-star" />

            </v-expansion-panel-title>
            <v-expansion-panel-text>
                A solution that is found by BRISE ({{ solutionState.solution ? 'Done' : 'Please stand by..' }})
            </v-expansion-panel-text>
            <v-expansion-panel-text>
                <v-list class="solution" v-if="solutionState.solution">
                    <v-list-item prepend-icon="mdi-flag">
                        <span class="desc">Configuration: </span> <span>{{ solutionState.configWithNones }}</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-grade">
                        <span class="desc">Result: </span> <span>{{ solutionState.result }}</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-network">
                        <span class="desc">Quality gain: </span>
                        <span>{{ formatPercent(100 * (dc[0] - sol[0]) / dc[0]) }}
                            %</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-blur">
                        <span class="desc">Performed measurements: </span>
                        <span>{{ solutionState.solution['performed_measurements'] }}</span>
                    </v-list-item>

                    <!--  <v-list-item v-if="searchspace['size'] != 'Infinity'">
                        <span class="desc">Saved efforts: </span>
                        <span>
                            {{
                                formatPercent((1 - solution['performed_measurements'] /
                                    ((searchspace['size'] as any) *
                                        (experiment_description as
                                            any)?.['RepetitionManager']?.['Instance']?.['AcceptableErrorBased']?.['MaxTasksPerConfiguration'])
                                ) * 100
                                ) }} %
                        </span>

                    </v-list-item> -->
                </v-list>
            </v-expansion-panel-text>
        </v-expansion-panel>
    </v-expansion-panels>

    <!-- Snackbar global -->
    <v-snackbar v-model="snackbar" :timeout="duration">
        {{ snackbarMsg }}
    </v-snackbar>
</template>