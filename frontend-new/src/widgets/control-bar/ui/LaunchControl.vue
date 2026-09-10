<script setup lang="ts">
import '@mdi/font/css/materialdesignicons.css'
import { onMounted, computed } from 'vue'


// download feature
import { DownloadPopup } from '../../../features/download-popup'

import { useLaunchControl } from '../model/use-control-bar'
import { resolveScenarioLabel } from '../../../entities/experiment/lib/resolve-exp-label'

const {
  isRunning,
  isFinish,
  showDownload,
  selectedFile,
  experiment_description,
  isConnected,
  openDownloadOption,

  startMainControl,
  stopMainControl,
  uploadFile } = useLaunchControl()



const scenarioLabel = computed(() =>
  resolveScenarioLabel(experiment_description.value?.Context?.TaskConfiguration?.Scenario)
)
</script>
<template>
  <div class="button-row">
    <v-card flat border rounded="lg">
      <v-card-item class="mb-2">
        <div class="info-row">
          <span class="label">Experiment</span>
          <span class="value"> {{ experiment_description?.Context?.TaskConfiguration?.TaskName }}</span>
        </div>
      </v-card-item>
      <v-card-item>
        <div class="info-row">
          <span class="label">Scenario</span>
          <span class="value mono">{{ scenarioLabel }}</span>
        </div>
      </v-card-item>
      <v-card-actions>
        <v-btn :disabled="isRunning || !isConnected" :ripple="false" color="#A8D5A2" style="color: #2D6A27;"
          variant="elevated" prepend-icon="mdi-play" @click="startMainControl">
          Start
        </v-btn>
        <v-btn :ripple="false" :disabled="!isRunning" color="#F4B8B8" style="color: #8B2E2E;" variant="elevated"
          prepend-icon="mdi-stop" @click="stopMainControl">
          Stop
        </v-btn>
        <v-btn v-if="isFinish" :ripple="false" class="text-none text-body-small" append-icon="mdi-content-save"
          color="#B8C9F4" style="color: #2E3F8B;" variant="outlined" @click="openDownloadOption">
          Save Experiment
        </v-btn>
        <v-file-input v-model="selectedFile" />
        <v-btn @click="uploadFile">
          Upload Experiment
        </v-btn>
        <!--     <v-select v-model="selectedExperiment" :items="experiments">
                </v-select>
                <v-menu open-on-hover>

               </v-menu>
                <v-list>
                    <v-list-item v-for="(item, index) in experiments" :key="index" :value="index">
                        <v-list-item-title>{{ item }}</v-list-item-title>
                    </v-list-item>
                </v-list>-->
      </v-card-actions>

      <v-progress-linear v-if="isRunning" indeterminate color="#FF9800" height="4"
        style="position:absolute; bottom: 0; left: 0; right: 0;" />
    </v-card>
    <v-dialog v-model="showDownload" max-width="350">
      <DownloadPopup @close="showDownload = false" />
    </v-dialog>
  </div>
</template>

<style scoped>
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);

}

.label {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.822);
  font-weight: 650;
}

.value {
  font-size: 14px;
  color: var(--v-theme-on-surface);
}

.mono {
  font-family: monospace;
  font-size: 13px;
}

.btn-start {
  background: #A8D5A2;
  color: #2D6A27;
}

.btn-stop {
  background: #F4B8B8;
  color: #8B2E2E;
}

.btn-save {
  background: #B8C9F4;
  color: #354baa;
}
</style>