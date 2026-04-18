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
    <h1>BRISE Dashboard</h1>
  </div>
  <LaunchControl></LaunchControl>

</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 100%;
  height: auto;
}
</style>
