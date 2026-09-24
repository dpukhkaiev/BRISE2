<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useMainEventStore } from './entities/main/model/main.event.store'
import logo from './assets/logo.svg'
import { LaunchControl } from './widgets/control-bar'
import { InfoBoard } from './widgets/info-board'
import { TaskList } from './widgets/task-list'
import { MultiDim } from './widgets/charts/multi-dim'
import { ImpRes } from './widgets/charts/imp-res'
import { Heatmap } from './widgets/charts/heatmap'
// HeatmapReg is disabled: main-node never publishes a "predictions" message (see front_API.py's
// SUPPORTED_MESSAGES / APIMessageBuilder - "PREDICTIONS" is registered but nothing ever sends it),
// so the surrogate surface can never populate. Re-enable once main-node publishes predictions.
// import { HeatmapReg } from './widgets/charts/heatmap-reg'



const tab = ref('info')
const chartMenu = ref(false)

const searchSpaceEditorUrl = `http://${import.meta.env.VITE_SEARCHSPACE_EDITOR_HOST}:${import.meta.env.VITE_SEARCHSPACE_EDITOR_PORT}`
const waffleUrl = `http://${import.meta.env.VITE_WAFFLE_HOST}:${import.meta.env.VITE_WAFFLE_PORT}`


const visibleCharts = ref(['multidim', 'impres', 'heatmap'])
const drawer = ref(false)
const searchSpace = ref(false)


onMounted(() => {
  const store = useMainEventStore()
  store.initEvent()
  store.loadPlotly()
})

function openSearchSpace() {
  searchSpace.value = true
}
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
          value="searchspace-editor"
          prepend-icon="mdi-open-in-new"
          @click="openSearchSpace()"
        >
          Open Searchspace Editor
        </v-tab>
        <v-dialog
          v-model="searchSpace"
          width="90%"
        >
          <v-card title="Searchspace editor">
            <v-card-text>
              <iframe
                :src="searchSpaceEditorUrl"
                style="width: 100%; height: 70vh; border: none;"
              />
            </v-card-text>

            <v-card-actions>
              <v-spacer />

              <v-btn
                text="Close Dialog"
                @click="searchSpace = false"
              />
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-tab
          value="waffle"
          prepend-icon="mdi-open-in-new"
          :href="waffleUrl"
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
          <!-- 'heatmap-reg' intentionally omitted, see HeatmapReg import comment above -->
          <v-list-item
            v-for="chart in [
              { id: 'multidim', label: 'Multi-dim' },
              { id: 'impres', label: 'Imp-res' },
              { id: 'heatmap', label: 'Heatmap' }
            ]"
            :key="chart.id"
          >
            <v-checkbox
              v-model="visibleCharts"
              :value="chart.id"
              :label="chart.label"
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
          title="Create Searchspace"
          @click="openSearchSpace(); drawer = false"
        />
        <v-list-item
          title=" Waffle"
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

          <v-tabs-window-item
            value="charts"
            eager
          >
            <v-row no-gutters>
              <v-col
                v-show="visibleCharts.includes('impres')"
                cols="12"
                md="8"
                class="pr-2"
              >
                <ImpRes />
              </v-col>
              <v-col
                v-show="visibleCharts.includes('heatmap')"
                cols="12"
                md="8"
                class="pr-2"
              >
                <Heatmap />
              </v-col>
              <v-col
                v-show="visibleCharts.includes('multidim')"
                cols="12"
                md="10"
                class="pr-2"
              >
                <MultiDim />
              </v-col>
              <!-- HeatmapReg is not rendered, see HeatmapReg import comment above -->
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
