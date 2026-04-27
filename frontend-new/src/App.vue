<script setup lang="ts">
import { onMounted } from 'vue'
import { useMainEventStore } from './entities/main/model/main.event.store'
import logo from './assets/logo.svg'
import { LaunchControl } from './widgets/control-bar'
import { InfoBoard } from './widgets/info-board'
import { TaskList } from './widgets/task-list'
import { MultiDim } from './widgets/charts/multi-dim'
import { ImpRes } from './widgets/charts/imp-res'
import { Heatmap } from './widgets/charts/heatmap'


const store = useMainEventStore()

onMounted(() => {
  store.initEvent()
})

</script>

<template>
  <div class="header">
    <img :src="logo" alt="BRISE Logo" />
    <div class="title-container">
      <p class="font-weight-black">BRISE Dashboard</p>

      <span class="description">A Software Product Line for Expensive Blackbox Optimization</span>
    </div>
  </div>

  <v-container fluid class="px-2 py-2">
    <v-row>
      <v-col cols="12" md="6">
        <div class="mb-4">
          <LaunchControl />
        </div>
        <TaskList />
      </v-col>

      <v-col cols="6" md="6">
        <InfoBoard />
      </v-col>
    </v-row>
    <MultiDim />
    <ImpRes />
    <Heatmap />
  </v-container>
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
