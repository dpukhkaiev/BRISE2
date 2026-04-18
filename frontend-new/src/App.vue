<script setup lang="ts">
import { onMounted } from 'vue'
import { useMainEventStore } from './entities/main/model/main.event.store'
import logo from './assets/logo.svg'
import LaunchControl from './widgets/control-bar/ui/LaunchControl.vue'
const store = useMainEventStore()

onMounted(() => {
  store.initEvent()
})

</script>

<template>
  <div class="header">
    <img :src="logo" alt="BRISE Logo" />
    <div class="title-container">
      <h1>BRISE Dashboard</h1>
      <span class="description">A Software Product Line for Expensive Blackbox Optimization</span>
    </div>
  </div>
  <LaunchControl></LaunchControl>

</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-container h1 {
  color: #d40eb3;
}

.title-container {
  display: flex;
  flex-direction: column;
}

.description {
  color: #c8469c;
  font-size: 0.9rem;
  font-style: bold;

}

.logo {
  width: 100%;
  height: auto;
}
</style>
