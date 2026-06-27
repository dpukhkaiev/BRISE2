<script setup lang="ts">
//store
import { useGraphStore } from '../store.ts'
import { useXmlToWfl } from '../composables/useXmlToWaffle'
import { computed } from 'vue'

defineProps<{ isOpen: boolean }>()
defineEmits(['toggle'])

const graphStore = useGraphStore()
const { convert } = useXmlToWfl()

const wflCode = computed(() => {
  const xml = graphStore.exportGraphToXML()
  return convert(xml)
})
</script>

<template>
  <div :class="['wfl-panel', { 'wfl-panel-closed': !isOpen }]">
    <button class="toggle-btn" @click="$emit('toggle')">
      <span class="btn-text">{{ isOpen ? 'Close Code View' : 'Open Code View' }}</span>
    </button>
    <div class="panel-content">
      <h3>Generated WFL Code</h3>
      <pre class="wfl-code">{{ wflCode }}</pre>
    </div>
  </div>
</template>

<style scoped>
.wfl-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 35vh;
  width: 100%;
  background-color: #ffffff;
  box-shadow: 0 -5px 15px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-direction: column;
  border-top: 1px solid #e2e8f0;
  color: #0f172a;
  padding: 0 20px 20px 20px;
  box-sizing: border-box;
  z-index: 100;
  display: flex;
  overflow-y: auto;
}

.wfl-panel-closed {
  transform: translateY(calc(100% - 40px));
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;

  width: 100%;
  padding: 10px 0;
  background: none;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  color: #0f172a;
  font-weight: 500;
  font-size: 14px;
  transition: background-color 0.2s, color 0.2s;
}

.toggle-btn:hover {
  background-color: #6aacee;
  color: #0f172a;
}

.arrow-icon {
  font-size: 16px;
  transform: translateY(0);
  transition: transform 0.2s;
}

.toggle-btn:hover .arrow-icon {
  transform: translateY(2px);
}

.panel-content {
  overflow-y: auto;
  flex-grow: 1;
  padding-top: 15px;
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
  margin: 0;
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