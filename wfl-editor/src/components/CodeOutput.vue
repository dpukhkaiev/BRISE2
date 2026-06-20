<script setup lang="ts">
defineProps<{ isOpen: boolean, code: string }>()
defineEmits(['close'])
</script>

<template>
  <div :class="['wfl-panel', {'wfl-panel-closed' : !isOpen}]">
      <button class="close-btn" @click="$emit('close')">✕</button>
      <h3>Generated WFL Code</h3>
      <pre class="wfl-code">{{ code }}</pre>
  </div>
</template>

<style scoped>
.wfl-overlay {
  position: absolute;
  left: 0;
  top : 0;
   height: 100%;
  width: 300px;
  background-color: #ffffff;
  box-shadow: 5px 0 15px rgba(0, 0, 0, 0.1);
  transition: transform 0.25s ease-out;
  background: rgba(0,0,0,0.5);
  border-right: 1px solid #e2e8f0;
  color: #1e293b;
  padding: 20px;
  box-sizing: border-box;
  z-index: 100;
  overflow-y: auto;
}

.wfl-code {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 6px;
  font-family: monospace;
  white-space: pre-wrap;
  overflow-x: auto;
   font-size: 12px;
}
.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
   color: #64748b;
}
</style>