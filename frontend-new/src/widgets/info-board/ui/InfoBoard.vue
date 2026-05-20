<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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

const duration = 3000
const snackbar = ref(false)
const snackbarMsg = ref('')

function refresh(): void {
    solution.value = undefined
    news.value = []
}

function initMainEvents(): void {
    // Main events
    store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'configuration') {
            let obj = JSON.parse(message.body)
            default_configuration = obj[0]
            let temp: NewsPoint = { 'time': Date.now(), 'message': 'Default configuration results received' }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            //news.value.push(temp)
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
            if (!default_configuration) {
                console.warn('default_configuration not set yet')
                dc = []
            } else {
                dc = Object.values(default_configuration.results)
            }
            configWithNones.value = configWithNones.value.replace(",,", ",None,")
            // NewsPOint type everywhere?
            let temp: NewsPoint = {
                'time': Date.now(),
                'message': '★★★ The optimum result is found. The best point is reached ★★★'
            }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            news.value.push(temp)
            if (news.value.length > 30) news.value.shift()
        }
    });

    // For information messages
    store.onEvent(MainEvent.LOG)?.subscribe((message: any) => {
        if (message.headers['message_subtype'] === 'info' || message.headers['message_subtype'] === 'error') {
            let obj = JSON.parse(message.body)
            let temp = { 'time': Date.now(), 'message': obj }
            snackbarMsg.value = temp['message']
            snackbar.value = true
            news.value.push(temp)
        }
    });

    // oldValue, newValue?
    watch(experiment_description, () => {
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
        news.value.push(temp)
    },
        // reactive object from store, need deep to tracl properties of the object
        { deep: true })
    store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
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
            snackbarMsg.value = temp['message']
            snackbar.value = true
            news.value.push(temp)
        }
    });
}

onMounted(() => {
    initMainEvents()
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
        <v-expansion-panel :disabled="!solution">
            <v-expansion-panel-title>
                Solution

                <v-icon icon="mdi-star" />

            </v-expansion-panel-title>
            <v-expansion-panel-text>
                A solution that is found by BRISE ({{ solution ? 'Done' : 'Please stand by..' }})
            </v-expansion-panel-text>
            <v-expansion-panel-text>
                <v-list class="solution" v-if="solution">
                    <v-list-item prepend-icon="mdi-flag">
                        <span class="desc">Configuration: </span> <span>{{ configWithNones }}</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-grade">
                        <span class="desc">Result: </span> <span>{{ result }}</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-network">
                        <span class="desc">Quality gain: </span>
                        <span>{{ formatPercent(100 * (dc[0] - sol[0]) / dc[0]) }}
                            %</span>
                    </v-list-item>

                    <v-list-item prepend-icon="mdi-blur">
                        <span class="desc">Performed measurements: </span>
                        <span>{{ solution['performed_measurements'] }}</span>
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