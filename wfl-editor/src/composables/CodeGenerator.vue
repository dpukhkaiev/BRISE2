<script lang="ts">
import type { Node, Edge } from '@vue-flow/core'
import { ref, computed } from 'vue'
import { useGraphStore } from '../store.ts'
import { storeToRefs } from 'pinia'


const graphStore = useGraphStore()

const { activeNodeId } = storeToRefs(graphStore)
const activeNode = computed(() => graphStore.activeNode as any)

const experiment = ref('')

// get all nodes from the store which exist 
const getAllNodes = computed(() => {
    graphStore.nodes
})

const wflOutput = computed(() => {

})

function JsonToWfl() {

}

function copyCode() {

}

// activeNode from store has the info in json about the current node
</script>

<template>
    <div class="code-container">
        <div class="header">
            <span>waffle-output.wfl</span>
            <!-- <button @click="copyCode" class="copy-btn">Kopieren</button> -->
        </div>
        <pre><code>{{ wflOutput }}</code></pre>
    </div>
</template>

<style scoped>
.code-container {
    background: #1e1e1e;
    color: #dcdcdc;
    padding: 15px;
    border-radius: 8px;
    position: relative;
}

.header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-family: monospace;
    font-size: 12px;
    color: #888;
}

.copy-btn {
    background: #333;
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
}

.copy-btn:hover {
    background: #444;
}

pre {
    margin: 0;
    overflow-x: auto;
}
</style>