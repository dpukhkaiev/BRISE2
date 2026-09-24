<script setup lang="ts">
import { computed, onMounted, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
// Constant
import { MainEvent } from '../../../entities/main'

//service
import { useMainEventStore } from '../../../entities/main'

import { Subscription } from 'rxjs'

import { useInfoBoard } from '../model/use-info-board'
import { normalizeConfigKeys, parseJsonWithInfinity, stringifyWithInfinity } from '../../../shared/lib'
// initialize store
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, experimentFinished } = storeToRefs(store)


const {
  news,
  visibleNews,
  newsExpanded,
  snackbar,
  snackbarMsg,
  solutionState,
  sol,
  dc,
  default_configuration,
  pushNews,
  toggleNewsExpanded,
  triggerSnackbar,
  refresh,
  formatPercent,
  computeQualityGain
} = useInfoBoard()

const isMinimization = computed<boolean>(() => {
  const objectives = experiment_description.value?.['Context']?.['TaskConfiguration']?.['Objectives'] as any
  if (!objectives) return true
  const firstObjectiveKey = Object.keys(objectives)[0]
  return objectives?.[firstObjectiveKey]?.['Minimization'] ?? true
})

const duration = 3000

const subscriptions = new Subscription()

let stopWatch: () => void = () => { }

function initMainEvents(): void {
  // Main events
  subscriptions.add(store.onEvent(MainEvent.DEFAULT)?.subscribe((message: any) => {
    if (message.headers['message_subtype'] === 'configuration') {
      let obj = parseJsonWithInfinity(message.body)

      default_configuration.value = obj[0]
      let temp = { 'time': Date.now(), 'message': 'Default configuration results received' }
      triggerSnackbar(temp.message)
      //SpushNews(temp.message)
      // snackbar.open(temp['message'], '×', {
      //   duration: 3000
      // });
    }

  })
  );

  subscriptions.add(store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
    if (message.headers['message_subtype'] === 'configuration') {
      let obj = parseJsonWithInfinity(message.body)
      const s = obj[0]
      const cleanConfigObj = normalizeConfigKeys(s?.configurations ?? {})
      const config = stringifyWithInfinity(cleanConfigObj, 2)

      if (!default_configuration.value) {
        console.warn('default_configuration not set yet')
        dc.value = []
        // why should I reset sol too?
        sol.value = []
      } else {
        dc.value = Object.values(default_configuration.value.results)
        sol.value = Object.values(s?.results ?? {})
      }

      solutionState.value = {
        solution: s,
        configWithNones: config,
        result: stringifyWithInfinity(s?.results)
      }
      let temp = {
        'time': Date.now(),
        'message': '★★★ The optimum result is found. The best point is reached ★★★'
      }
      triggerSnackbar(temp.message)
      pushNews(temp.message)

    }
  })
  );

  // For information messages
  subscriptions.add(store.onEvent(MainEvent.LOG)?.subscribe((message: any) => {
    if (experimentFinished.value) return
    if (message.headers['message_subtype'] === 'info' || message.headers['message_subtype'] === 'error') {
      let obj = parseJsonWithInfinity(message.body)
      let temp = { 'time': Date.now(), 'message': obj }
      triggerSnackbar(temp.message)
      pushNews(temp.message)
    }
  })
  );

  // oldValue, newValue?
  stopWatch = watch(experiment_description, () => {
    console.log('experiment_description:', stringifyWithInfinity(experiment_description.value, 2))
    refresh()
    /* if (searchspace.value && searchspace.value['size']) {
         searchspace.value['size'] = parseFloat(searchspace.value['size'])
     }*/
    let temp = {
      'time': Date.now(),
      'message': 'The main configurations of the experiment are obtained. Let\'s go! '
    }
    triggerSnackbar(temp.message)
    pushNews(temp.message)
  },
    // reactive object from store, need deep to trace properties of the object
    { deep: true })

  subscriptions.add(store.onEvent(MainEvent.NEW)?.subscribe((message: any) => {
    if (experimentFinished.value) return
    if (message.headers['message_subtype'] === 'configuration') {
      let configs = parseJsonWithInfinity(message.body)
      configs.forEach((configuration: any) => {
        if (configuration?.configurations) {
          const cleanConfig = normalizeConfigKeys(configuration.configurations)
          const cleanResults = configuration.results ?? {}
          let temp = {
            'time': Date.now(),
            'message': 'New results for ' + stringifyWithInfinity(cleanConfig) + ' → ' + stringifyWithInfinity(cleanResults)
          }
          triggerSnackbar(temp.message)
          pushNews(temp.message)
        } else {
          console.log("Empty configuration")
        }
      })
    }
  })
  );

  // NOTE: main-node does not currently emit a "predictions" message at all, so this handler is presently dead code 
  // pending a rework.
  subscriptions.add(store.onEvent(MainEvent.PREDICTIONS)?.subscribe((message: any) => {
    if (experimentFinished.value) return
    if (message.headers['message_subtype'] === 'configurations') {
      let obj = parseJsonWithInfinity(message.body)
      let temp = {
        'time': Date.now(),
        'message': 'Prediction obtained. ' + obj.length + ' predictions'
      }
      triggerSnackbar(temp.message)
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



</script>

<template>
  <v-expansion-panels
    elevation="2"
    multiple
  >
    <!-- Panel 1 -->
    <v-expansion-panel :disabled="news.length === 0">
      <v-expansion-panel-title class="info">
        Info messages

        <v-icon
          icon="mdi-text-box"
          class="mx-2"
        />
        <p class="ml-4">
          Basic information from the workflow of experiments ({{ news ? news.length : "0" }})
        </p>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <!-- Logs list -->

        <v-list
          v-if="news.length != 0"
          lines="two"
        >
          <v-list-item
            v-for="i in visibleNews.length"
            :key="visibleNews[visibleNews.length - i].id"
            prepend-icon="mdi-check"
          >
            <v-list-item-title>{{ visibleNews[visibleNews.length - i].message }}</v-list-item-title>
            <v-list-item-subtitle>
              {{ new Date(visibleNews[visibleNews.length - i].time).toLocaleString() }}
            </v-list-item-subtitle>
            <v-divider />
          </v-list-item>
        </v-list>

        <v-btn
          v-if="news.length > 30"
          variant="text"
          size="small"
          @click="toggleNewsExpanded"
        >
          {{ newsExpanded ? 'Show recent only' : `Show all (${news.length})` }}
        </v-btn>
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
        <v-list
          v-if="solutionState.solution"
          class="solution"
        >
          <v-list-item prepend-icon="mdi-flag">
            <span class="desc">Configuration: </span> <span>{{ solutionState.configWithNones }}</span>
          </v-list-item>

          <v-list-item prepend-icon="mdi-grade">
            <span class="desc">Result: </span> <span>{{ solutionState.result }}</span>
          </v-list-item>

          <v-list-item
            v-if="dc.length && sol.length"
            prepend-icon="mdi-network"
          >
            <span class="desc">Quality gain: </span>
            <span>{{ formatPercent(computeQualityGain(dc[0], sol[0], isMinimization)) }}{{ computeQualityGain(dc[0], sol[0], isMinimization) === null ? '' : ' %' }}</span>
          </v-list-item>

          <v-list-item prepend-icon="mdi-blur">
            <span class="desc">Performed measurements: </span>
            <span>{{ solutionState.solution['performed_measurements'] }}</span>
          </v-list-item>
        </v-list>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>

  <!-- Snackbar global -->
  <v-snackbar
    v-model="snackbar"
    :timeout="duration"
  >
    {{ snackbarMsg }}
  </v-snackbar>
</template>