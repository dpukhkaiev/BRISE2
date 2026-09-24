<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from './entities/main/model/main.event.store'
import { usePlotStore } from './entities/main/model/plot.store'
import logo from './assets/logo.svg'
import { LaunchControl } from './widgets/control-bar'
import { InfoBoard } from './widgets/info-board'
import { TaskList } from './widgets/task-list'
import type { ExperimentDescription } from './entities/experiment/model/experiment.model'

import { Skeleton } from './widgets/charts/skeleton-chart'

import { OptHist } from './widgets/charts/opt-hist'
import { HypImp } from './widgets/charts/hyp-imp'
import { ParaCoord } from './widgets/charts/para-coord'
import { ParetoFront } from './widgets/charts/pareto-front'
import { Slice } from './widgets/charts/slice'
import { Rank } from './widgets/charts/rank'
import { Contour } from './widgets/charts/contour'
import { Edf } from './widgets/charts/edf'

function isContourParameter(
    parameter: string,
    experimentDescription: ExperimentDescription
): boolean {
    const searchSpace =
        experimentDescription.Context?.SearchSpace?.[parameter];

    if (!searchSpace) {
        return false;
    }

    // Float / Integer
    if (
        searchSpace.Type === "FloatHyperparameter" ||
        searchSpace.Type === "IntegerHyperparameter"
    ) {
        return true;
    }

    // Nominal / Ordinal
    if (
        searchSpace.Type === "NominalHyperparameter" ||
        searchSpace.Type === "OrdinalHyperparameter"
    ) {
        return (
            Array.isArray(searchSpace.Categories) &&
            searchSpace.Categories.length >= 2
        );
    }

    return false;
}

const store = useMainEventStore()
const plotStore = usePlotStore()
const { selected, visibleCharts, canChangeVisibleCharts } = storeToRefs(plotStore)
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

//compute parameters for Parallel Coordinates dropdown options
const paraCoordParameterNames = computed(() => {
    if (!experiment_description.value) {
      return []
    }
    const searchSpace =
        experiment_description.value?.Context?.SearchSpace ?? {};

    let allParams = Object.entries(searchSpace)
        .filter(([name, value]) =>
            name !== "Structure" &&
            typeof value === "object" &&
            value !== null &&
            "Type" in value
        )
        .map(([name]) => name);
    let contourParams: string[] = []
    for (var param of allParams) {
      if (isContourParameter(param, experiment_description.value)) {
        contourParams.push(param)
      }
    }
    return contourParams
})

// manage selected dropdown values
const optHistObjective = ref("")
const selectedOptHistObjective = computed(() => {
    return optHistObjective.value || objectiveNames.value[0] || ""
})

const paraCoordParams = ref<string[]>([])
const selectedParaCoordParams = computed(() => {
    return paraCoordParams.value.length
        ? paraCoordParams.value
        : parameterNames.value.slice(0, 1)
})
const paraCoordObjective = ref("")
const selectedParaCoordObjective = computed(() => {
    return paraCoordObjective.value || objectiveNames.value[0] || ""
})

const rankParam1 = ref("")
const selectedRankParam1 = computed(() => {
    return rankParam1.value || parameterNames.value[0] || ""
})
const rankParam2 = ref("")
const selectedRankParam2 = computed(() => {
    return rankParam2.value || parameterNames.value[1] || ""
})
const rankObjective = ref("")
const selectedRankObjective = computed(() => {
    return rankObjective.value || objectiveNames.value[0] || ""
})

const sliceParam = ref("")
const selectedSliceParam = computed(() => {
    return sliceParam.value || parameterNames.value[0] || ""
})
const sliceObjective = ref("")
const selectedSliceObjective = computed(() => {
    return sliceObjective.value || objectiveNames.value[0] || ""
})

const hypImpParams = ref<string[]>([])
const selectedHypImpParams = computed(() => {
    return hypImpParams.value.length
        ? hypImpParams.value
        : parameterNames.value.slice(0, 1)
})
const hypImpObjective = ref("")
const selectedHypImpObjective = computed(() => {
    return hypImpObjective.value || objectiveNames.value[0] || ""
})

const paretoObjective1 = ref("")
const selectedParetoObjective1 = computed(() => {
    return paretoObjective1.value || objectiveNames.value[0] || ""
})
const paretoObjective2 = ref("")
const selectedParetoObjective2 = computed(() => {
    return paretoObjective2.value || objectiveNames.value[1] || ""
})
const onlyShowParetoFront = ref(false)

const contourParam1 = ref("")
const selectedContourParam1 = computed(() => {
    return contourParam1.value || paraCoordParameterNames.value[0] || ""
})
const contourParam2 = ref("")
const selectedContourParam2 = computed(() => {
    return contourParam2.value || paraCoordParameterNames.value[1] || ""
})
const contourObjective = ref("")
const selectedContourObjective = computed(() => {
    return contourObjective.value || objectiveNames.value[0] || ""
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
        rankObjective.value = objectives[0] ?? ""
        sliceObjective.value = objectives[0] ?? ""
        hypImpObjective.value = objectives[0] ?? ""
        paretoObjective1.value = objectives[0] ?? ""
        paretoObjective2.value = objectives[1] ?? ""
        onlyShowParetoFront.value = false
        contourObjective.value = objectives[0] ?? ""
    },
    { immediate: true }
)

watch(
    parameterNames,
    (parameters) => {
        paraCoordParams.value = [...parameters]
        rankParam1.value = parameters[0] ?? ""
        rankParam2.value = parameters[1] ?? ""
        sliceParam.value = parameters[0] ?? ""
        hypImpParams.value = [...parameters]
    },
    { immediate: true }
)

watch(
    paraCoordParameterNames,
    (params) => {
        contourParam1.value = params[0] ?? ""
        contourParam2.value = params[1] ?? ""
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
              :disabled="!canChangeVisibleCharts"
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
                    class="user-input"
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
                  class="user-input"
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
                      :disabled="paraCoordParams.length === 1 && paraCoordParams.includes(param)"
                    />
                  </v-list-item>
                </v-list>
                <v-select
                    v-model="paraCoordObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
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
                <v-select
                    v-model="rankParam1"
                    :items="parameterNames"
                    label="Parameter 1"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="rankParam2"
                    :items="parameterNames"
                    label="Parameter 2"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="rankObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <Rank
                    :rankParam1="selectedRankParam1"
                    :rankParam2="selectedRankParam2"
                    :rankObjective="selectedRankObjective"
                />
              </v-col>

              <v-col
                v-if="selected['Hyperparameter Importances']"
                v-show="visibleCharts.includes('Hyperparameter Importances')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-list
                  density="compact"
                  min-width="180"
                  class="user-input"
                >
                  <v-list-subheader>Parameters</v-list-subheader>
                  <v-list-item
                    v-for="param in parameterNames"
                    :key="param"
                  >
                    <v-checkbox
                      v-model="hypImpParams"
                      :value="param"
                      :label="param"
                      density="compact"
                      hide-details
                      color="green-darken-2"
                    />
                  </v-list-item>
                </v-list>
                <v-select
                    v-model="hypImpObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <HypImp
                    :hypImpParams="selectedHypImpParams"
                    :hypImpObjective="selectedHypImpObjective"
                />
              </v-col>

              <v-col
                v-if="selected['Slice Plot']"
                v-show="visibleCharts.includes('Slice Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-select
                    v-model="sliceParam"
                    :items="parameterNames"
                    label="Parameter"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="sliceObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <Slice
                    :sliceParam="selectedSliceParam"
                    :sliceObjective="selectedSliceObjective"
                />
              </v-col>

              <v-col
                v-if="selected['Contour Plot']"
                v-show="visibleCharts.includes('Contour Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-select
                    v-model="contourParam1"
                    :items="paraCoordParameterNames"
                    label="Parameter 1"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="contourParam2"
                    :items="paraCoordParameterNames"
                    label="Parameter 2"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="contourObjective"
                    :items="objectiveNames"
                    label="Objective"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <Contour
                    :contourParam1="selectedContourParam1"
                    :contourParam2="selectedContourParam2"
                    :contourObjective="selectedContourObjective"
                />
              </v-col>

              <v-col
                v-if="selected['Pareto Front']"
                v-show="visibleCharts.includes('Pareto Front')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <v-select
                    v-model="paretoObjective1"
                    :items="objectiveNames"
                    label="Objective 1"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-select
                    v-model="paretoObjective2"
                    :items="objectiveNames"
                    label="Objective 2"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="user-input"
                />
                <v-switch
                    v-model="onlyShowParetoFront"
                    label="Show only Pareto front"
                    color="primary"
                    hide-details
                    class="user-input"
                />
                <ParetoFront
                    :paretoObjective1="selectedParetoObjective1"
                    :paretoObjective2="selectedParetoObjective2"
                    :only-show-pareto-front="onlyShowParetoFront"
                />
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

.user-input {
  margin: 10px
}
</style>
