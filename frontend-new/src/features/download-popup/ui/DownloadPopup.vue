<script setup lang="ts">
import { downloadPopUp } from '../api/download.api'
const emit = defineEmits(['close'])

async function download(format: string) {
    await downloadPopUp(format)
    emit('close')
}
</script>

<template>
  <v-card
    class="mx-auto pa-4"
    min-width="300"
  >
    <v-card-title class="text-h6 mb-4">
      Download
    </v-card-title>
    <v-card-actions class="flex-column ga-2">
      <v-btn
        block
        variant="elevated"
        color="#B8C9F4"
        style="color: #2E3F8B;"
        prepend-icon="mdi-file"
        @click="download('pkl')"
      >
        Experiment instance
      </v-btn>
      <v-btn
        block
        variant="elevated"
        color="#A8D5A2"
        style="color: #2D6A27;"
        prepend-icon="mdi-table"
        @click="download('csv')"
      >
        Basic metrics
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.d-variant {
    text-align: center;
}

.d-item {
    margin: 0 35px;
}
</style>