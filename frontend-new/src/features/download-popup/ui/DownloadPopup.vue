<script setup lang="ts">
import { downloadPopUp } from '../api/download.api'
const emit = defineEmits(['close'])

async function download(format: string) {
    await downloadPopUp(format)
    emit('close')
}
</script>

<template>
    <div class="download-container">
        <h2>Download</h2>
        <button @click="download('pkl')" class="btn-download">
            Experiment instance
        </button>
        <button @click="download('csv')" class="btn-download">
            Basic metrics
        </button>

    </div>
</template>

<style scoped>
.d-variant {
    text-align: center;
}

.d-item {
    margin: 0 35px;
}
</style>