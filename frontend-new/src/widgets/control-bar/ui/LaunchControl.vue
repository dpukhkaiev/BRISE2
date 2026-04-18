<script setup lang="ts">
import '@mdi/font/css/materialdesignicons.css'
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
// services
import { useMainEventStore } from '../../../entities/main/model/main.event.store'
import { MainClientApi } from '../../../entities/main/api/main.client.store'
//data
import { MainEvent } from '../../../entities/main/model/main.types'


// download feature
import { DownloadPopup } from '../../../features/download-popup'
const isRunning = ref(false)
// Flag for finish experiment
const isFinish = ref(false)

// create a store 
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description } = storeToRefs(store)

const showDownload = ref(false)

function openDownloadOption(): void {
    showDownload.value = true
}

function startMainControl(): any {
    if (isRunning.value === false) {
        stopMainControl();
        MainClientApi.startMain();
        isRunning.value = true
        isFinish.value = false
    }
}

function stopMainControl(): any {
    if (isRunning.value === true) {
        MainClientApi.stopMain();
        isRunning.value = false;
    }

}

function initMainEvents(): void {
    store.onEvent(MainEvent.FINAL)?.subscribe((message: any) => {
        isRunning.value = false;
        isFinish.value = true;
    })

}


onMounted(() => {
    initMainEvents()
})
</script>
<template>
    <div class="button-row">
        <v-card class="mx-auto" color="#eeee" max-width="650" min-height="350">
            <v-card-item>
                <div class="experiment">
                    <h2>Experiment</h2>
                    <span> {{ experiment_description?.Context?.TaskConfiguration?.TaskName }}</span>
                </div>
            </v-card-item>
            <v-card-item>
                <div class="scenario">
                    <span>Scenario </span>
                    <span>{{ experiment_description?.Context?.TaskConfiguration?.Scenario?.ws_file }}</span>
                </div>
            </v-card-item>
            <v-card-actions>
                <v-btn :disabled="isRunning" @click="startMainControl">
                    Start
                </v-btn>
                <v-btn :disabled="!isRunning" @click="stopMainControl">
                    Stop
                </v-btn>
                <v-btn class="text-none text-body-large" v-if="isFinish" @click="openDownloadOption"
                    append-icon="mdi-content-save" color="#5865f2" size="small">

                    Save Experiment

                </v-btn>

            </v-card-actions>
        </v-card>
        <v-bottom-sheet v-model="showDownload">
            <DownloadPopup @close="showDownload = false" />
        </v-bottom-sheet>

        <v-progress-linear v-if="isRunning" indeterminate color="#FF9800" />
    </div>
</template>