<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from './entities/main/model/main.event.store'
import { usePlotStore } from './entities/main/model/plot.store'
import logo from './assets/logo.svg'
import { LaunchControl } from './widgets/control-bar'
import { InfoBoard } from './widgets/info-board'
import { TaskList } from './widgets/task-list'

import { Skeleton } from './widgets/charts/skeleton-chart'
//import { Heatmap } from './widgets/charts/heatmap'

import { OptHist } from './widgets/charts/opt-hist'
import { HypImp } from './widgets/charts/hyp-imp'
import { ParaCoord } from './widgets/charts/para-coord'
import { ParetoFront } from './widgets/charts/pareto-front'
import { Slice } from './widgets/charts/slice'
import { Rank } from './widgets/charts/rank'
import { Contour } from './widgets/charts/contour'
import { Edf } from './widgets/charts/edf'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { selected, visibleCharts } = storeToRefs(plotStore)
const { experiment_description } = storeToRefs(store)


const tab = ref('info')
const chartMenu = ref(false)

const drawer = ref(false)
const selectedCharts = computed(() =>
  Object.keys(selected.value).filter(
    (chart) => selected.value[chart as keyof typeof selected.value]
  )
)

// compute objectives of the experiment for dropdown options
const objectiveNames = computed(() =>
    Object.keys(
        experiment_description.value?.Context?.TaskConfiguration?.Objectives ?? {}
    )
)

// compute parameters of the experiment for dropdown options
const parameterNames = computed(() => {
    const searchSpace =
        experiment_description.value?.Context?.SearchSpace ?? {};

    return Object.entries(searchSpace)
        .filter(([name, value]) =>
            name !== "Structure" &&
            typeof value === "object" &&
            value !== null &&
            "Type" in value
        )
        .map(([name]) => name);
});

// manage selected dropdown values
const optHistObjective = ref("")
const selectedOptHistObjective = computed(() => {
    return optHistObjective.value || objectiveNames.value[0] || "";
})

const paraCoordParams = ref<string[]>([])
const selectedParaCoordParams = computed(() => {
    return paraCoordParams.value.length
        ? paraCoordParams.value
        : parameterNames.value.slice(0, 1)
})
const paraCoordObjective = ref("")
const selectedParaCoordObjective = computed(() => {
    return paraCoordObjective.value || objectiveNames.value[0] || "";
})

onMounted(() => {
  store.initEvent()
  store.loadPlotly()
})

// update default dropdown values on initialization and new experiment description
watch(
    objectiveNames,
    (objectives) => {
        optHistObjective.value = objectives[0] ?? ""
        paraCoordObjective.value = objectives[0] ?? ""
    },
    { immediate: true }
)

watch(
    parameterNames,
    (parameters) => {
        paraCoordParams.value = [...parameters]
    },
    { immediate: true }
)
</script>

<template>
  <v-app>
    <v-app-bar
      height="56"
      flat
      border="b"
    >
      <v-app-bar-nav-icon
        class="d-flex d-md-none"
        @click="drawer = !drawer"
      />
      <div class="d-flex align-center pl-3">
        <img
          :src="logo"
          alt="BRISE Logo"
          height="52"
        >
        <div class="d-flex flex-column ml-2">
          <div class="font-weight-medium">
            BRISE Dashboard
          </div>

          <div class=" text-green-darken-2 d-none d-md-block text-caption">
            Benchmark Reduction via Adaptive Instance
            Selection
          </div>
        </div>
      </div>

      <v-spacer />

      <v-tabs
        v-model="tab"
        color="green-darken-2"
        density="compact"
        class="d-none d-md-flex"
      >
        <v-tab
          value="info"
          prepend-icon="mdi-text-box"
        >
          Info
        </v-tab>

        <v-tab
          value="tasks"
          prepend-icon="mdi-format-list-checks"
        >
          Task List
        </v-tab>
        <v-tab
          value="waffle"
          prepend-icon="mdi-open-in-new"
          href="http://localhost:8000"
          target="_blank"
        >
          Open Waffle
        </v-tab>
        <v-tab
          value="charts"
          prepend-icon="mdi-chart-line"
        >
          Charts
        </v-tab>
      </v-tabs>
      <v-menu
        v-if="tab === 'charts'"
        v-model="chartMenu"
        :close-on-content-click="false"
      >
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            value="charts"
            prepend-icon="mdi-menu-down"
            density="compact"
          />
        </template>
        <v-list
          density="compact"
          min-width="180"
        >
          <v-list-subheader>Visible charts</v-list-subheader>
          <v-list-item
            v-for="chart in selectedCharts"
            :key="chart"
          >
            <v-checkbox
              v-model="visibleCharts"
              :value="chart"
              :label="chart"
              density="compact"
              hide-details
              color="green-darken-2"
            />
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-navigation-drawer
      v-model="drawer"
      temporary
    >
      <v-list nav>
        <v-list-item
          prepend-icon="mdi-text-box"
          title="Info"
          value="info"
          @click="tab = 'info'; drawer = false"
        />
        <v-list-item
          prepend-icon="mdi-format-list-checks"
          title="Task List"
          value="tasks"
          @click="tab = 'tasks'; drawer = false"
        />
        <v-list-item
          title="Waffle"
          @click="tab = 'waffle'; drawer = false"
        />
        <v-list-item
          prepend-icon="mdi-chart-line"
          title="Charts"
          value="charts"
          @click="tab = 'charts'; drawer = false"
        />
      </v-list>
    </v-navigation-drawer>
    <v-main>
      <v-container
        fluid
        class="pa-2"
      >
        <v-row
          no-gutters
          class="mb-4"
        >
          <v-col
            cols="12"
            md="8"
            class="pr-2"
          >
            <LaunchControl />
          </v-col>
        </v-row>
        <v-divider class="my-4" />
        <v-tabs-window v-model="tab">
          <v-tabs-window-item
            value="info"
            eager
          >
            <InfoBoard />
          </v-tabs-window-item>
          <v-tabs-window-item
            value="tasks"
            eager
          >
            <TaskList />
          </v-tabs-window-item>

          <v-tabs-window-item value="charts">
            <v-row no-gutters>
              <v-col
                cols="12"
                md="8"
                class="pr-2"
              >
                <Skeleton/>
              </v-col>
              <!--
              <v-col
                v-if="selected['Configuration Scatter Plot']"
                v-show="visibleCharts.includes('Configuration Scatter Plot')"
                cols="12"
                md="8"
                class="pr-2"
              >
                <select v-model="heatmapParam1">
                    <option
                        v-for="parameter in parameterNames"
                        :key="parameter"
                        :value="parameter"
                    >
                        {{ parameter }}
                    </option>
                </select>
                <select v-model="heatmapParam2">
                    <option
                        v-for="parameter in parameterNames"
                        :key="parameter"
                        :value="parameter"
                    >
                        {{ parameter }}
                    </option>
                </select>
                <Heatmap/>
              </v-col>
              -->
              <v-col
                v-if="selected['Optimization History']"
                v-show="visibleCharts.includes('Optimization History')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-select
                    v-model="optHistObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                />
                <OptHist :optHistObjective="selectedOptHistObjective" />
              </v-col>

              <v-col
                v-if="selected['Parallel Coordinates']"
                v-show="visibleCharts.includes('Parallel Coordinates')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-list
                  density="compact"
                  min-width="180"
                >
                  <v-list-subheader>Parameters</v-list-subheader>
                  <v-list-item
                    v-for="param in parameterNames"
                    :key="param"
                  >
                    <v-checkbox
                      v-model="paraCoordParams"
                      :value="param"
                      :label="param"
                      density="compact"
                      hide-details
                      color="green-darken-2"
                    />
                  </v-list-item>
                </v-list>
                <v-radio-group
                    v-model="paraCoordObjective"
                    label="Objective"
                    inline
                >
                    <v-radio
                        v-for="objective in objectiveNames"
                        :key="objective"
                        :label="objective"
                        :value="objective"
                    />
                </v-radio-group>
                <ParaCoord
                    :paraCoordParams="selectedParaCoordParams"
                    :paraCoordObjective="selectedParaCoordObjective"
                />
              </v-col>

              <v-col
                v-if="selected['Rank Plot']"
                v-show="visibleCharts.includes('Rank Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <Rank/>
              </v-col>

              <v-col
                v-if="selected['Hyperparameter Importances']"
                v-show="visibleCharts.includes('Hyperparameter Importances')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <HypImp/>
              </v-col>

              <v-col
                v-if="selected['Slice Plot']"
                v-show="visibleCharts.includes('Slice Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <Slice/>
              </v-col>

              <v-col
                v-if="selected['Contour Plot']"
                v-show="visibleCharts.includes('Contour Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <Contour/>
              </v-col>

              <v-col
                v-if="selected['Pareto Front']"
                v-show="visibleCharts.includes('Pareto Front')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <ParetoFront/>
              </v-col>

              <v-col
                v-if="selected['EDF Plot']"
                v-show="visibleCharts.includes('EDF Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <Edf/>
              </v-col>
            </v-row>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-container {
  display: flex;
  flex-direction: column;
}

.title-container p {
  font-size: 55px;
  font-weight: 450;
  line-height: 54px;
  letter-spacing: -0.25px;
  color: black;

}

.description {
  color: #2D6A27;
  font-size: 0.9rem;
  font-style: bold;

}

.logo {
  width: 100%;
  height: auto;
}
</style>
