<script setup lang="ts">
import { ref, markRaw } from 'vue'
// Vueflow
import type { Node, Edge } from '@vue-flow/core'
import { VueFlow, Panel, useVueFlow } from '@vue-flow/core'
// components
import Canvas from './components/Canvas.vue'





</script>

<template>
  <Canvas></Canvas>
</template>

<style>
.custom-center-panel {
  position: absolute;
  top: 20px;
  left: 50%;
  right: auto !important;
  transform: translateX(-50%);
  margin: 0;
  z-index: 50;
}
</style>