<script setup lang="ts">
import '@mdi/font/css/materialdesignicons.css'
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
// services
import { useMainEventStore } from '../../../entities/main'
import { MainClientApi } from '../../../entities/main'
//data
import { MainEvent } from '../../../entities/main'


// download feature
import { DownloadPopup } from '../../../features/download-popup'
const isRunning = ref(false)
// Flag for finish experiment
const isFinish = ref(false)

// create a store 
const store = useMainEventStore()
// destructure reactive value from main.event.store
const { experiment_description, searchspace, globalConfig } = storeToRefs(store)

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
    store.onEvent(MainEvent.FINAL)?.subscribe(() => {
        isRunning.value = false;
        isFinish.value = true;
    })

}
const selectedFile = ref<any>(null)

const uploadFile = async () => {

    console.log('selectedFile:', selectedFile.value)
    if (!selectedFile.value) return

    const file = selectedFile.value!

    const reader = new FileReader()
    reader.onload = () => {
        const clean = (reader.result as string).replace(/:\s*Infinity/g, ': null')
        const parsed = JSON.parse(clean)
        store.experiment_description = parsed.experiment_description
        store.searchspace = parsed.searchspace_description
        store.globalConfig = parsed.global_configuration
    }

    reader.readAsText(file)
}

onMounted(() => {
    initMainEvents()
})

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
                    <span class="value mono">{{ experiment_description?.Context?.TaskConfiguration?.Scenario?.ws_file
                        }}</span>
                </div>
            </v-card-item>
            <v-card-actions>
                <v-btn :ripple="false" :disabled="isRunning" @click="startMainControl" color="#A8D5A2"
                    style="color: #2D6A27;" variant="elevated" prepend-icon="mdi-play">
                    Start
                </v-btn>
                <v-btn :ripple="false" :disabled="!isRunning" @click="stopMainControl" color="#F4B8B8"
                    style="color: #8B2E2E;" variant="elevated" prepend-icon="mdi-stop">
                    Stop
                </v-btn>
                <v-btn :ripple="false" class="text-none text-body-small" v-if="isFinish" @click="openDownloadOption"
                    append-icon="mdi-content-save" color="#B8C9F4" style="color: #2E3F8B;" variant="outlined">
                    Save Experiment
                </v-btn>

                <v-file-input label="Select Experiment" density="compact" v-model="selectedFile"
                    placeholder="Select an experiment" color="deep-green-accent-2" variant="outlined"
                    style="position:relative">
                </v-file-input>
                <v-btn :ripple="false" color="#A8D5A2" style="color: #2D6A27;" @click="uploadFile">Select </v-btn>

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