<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useMainEventStore } from './entities/main/model/main.event.store'
import { usePlotStore } from './entities/main/model/plot.store'
import logo from './assets/logo.svg'
import { LaunchControl } from './widgets/control-bar'
import { InfoBoard } from './widgets/info-board'
import { TaskList } from './widgets/task-list'

import { Skeleton } from './widgets/charts/skeleton-chart'
import { Heatmap } from './widgets/charts/heatmap'

import { OptHist } from './widgets/charts/opt-hist'
import { HypImp } from './widgets/charts/hyp-imp'
import { ParaCoord } from './widgets/charts/para-coord'
import { ParetoFront } from './widgets/charts/pareto-front'
import { Slice } from './widgets/charts/slice'
import { Rank } from './widgets/charts/rank'
import { Contour } from './widgets/charts/contour'

const store = useMainEventStore()
const plotStore = usePlotStore()
const { selected, visibleCharts } = storeToRefs(plotStore)

const tab = ref('info')
const chartMenu = ref(false)
//const visibleCharts = ref(['multidim', 'impres', 'heatmap', 'hypImp'])
const drawer = ref(false)
const selectedCharts = computed(() =>
  Object.keys(selected.value).filter(
    (chart) => selected.value[chart as keyof typeof selected.value]
  )
)

onMounted(() => {
  store.initEvent()
  store.loadPlotly()
})

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

              <v-col
                cols="12"
                md="8"
                class="pr-2"
              >
                <Heatmap/>
              </v-col>

              <v-col
                v-if="selected['Optimization History']"
                v-show="visibleCharts.includes('Optimization History')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <OptHist/>
              </v-col>

              <v-col
                v-if="selected['Parallel Coordinates']"
                v-show="visibleCharts.includes('Parallel Coordinates')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <ParaCoord/>
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
                <!--<Edf/>-->
              </v-col>

              <v-col
                v-if="selected['Intermediate Values']"
                v-show="visibleCharts.includes('Intermediate Values')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <!--<IntVal/>-->
              </v-col>

              <v-col
                v-if="selected['Terminator Improvement']"
                v-show="visibleCharts.includes('Terminator Improvement')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <!--<TermImpr/>-->
              </v-col>

              <v-col
                v-if="selected['Timeline Plot']"
                v-show="visibleCharts.includes('Timeline Plot')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <!--<Timeline/>-->
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
