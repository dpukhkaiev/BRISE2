<script setup lang="ts">
import { ref, markRaw, watch } from 'vue'
// Vueflow
import type { Node, Edge } from '@vue-flow/core'
import { VueFlow, Panel, useVueFlow } from '@vue-flow/core'
// components
import Toolbar from './Toolbar.vue'
import NumericNode from '../nodes/NumericNode.vue'
import CategoricalNode from '../nodes/CategoricalNode.vue'
import Sidebar from './Sidebar.vue'
import Category from './Category.vue'
import CategoryNode from '../nodes/CategoryNode.vue'
import CodeOutput from './CodeOutput.vue'
//store
import { useGraphStore } from '../store.ts'

// desctructure nodes, edges here (no need of ref([]))
const { nodes: flowNodes, addEdges, onConnect, edges: flowEdges, addNodes } = useVueFlow()

const graphStore = useGraphStore()

// bind types with .vue components
const myNodeTypes = {
    float: markRaw(NumericNode),
    integer: markRaw(NumericNode),
    nominal: markRaw(CategoricalNode),
    ordinal: markRaw(CategoricalNode),
    category: markRaw(CategoryNode)
}

// sidebar state
const isSidebarOpen = ref(false)

// categories popup window state
const isCategoryTableOpen = ref(false)

onConnect((connection) => {

    const sourceNode = flowNodes.value.find((node: any) => node.id === connection.source)
    const targetNode = flowNodes.value.find((node: any) => node.id === connection.target)


    if (sourceNode && targetNode) {
        const isSourceCategorical = sourceNode.type === 'nominal' || sourceNode.type === 'ordinal'
       

    if (isSourceCategorical) {  
    
    const categoryNode = graphStore.createCategoryBox(sourceNode, targetNode)
            addNodes(categoryNode)

            addEdges({ source: sourceNode.id, target: categoryNode.id })
            addEdges({ source: categoryNode.id, target: targetNode.id })

            graphStore.addChildToNode(sourceNode.id, categoryNode.id)
            graphStore.addChildToNode(categoryNode.id, targetNode.id)
            graphStore.setEdges(flowEdges.value)
            return
    }
    }

    addEdges(connection)
    graphStore.setEdges(flowEdges.value)

})

// for store to track changes of the nodes
watch(flowNodes, (newNodes) => {
    graphStore.setNodes(newNodes)
}, { deep: true })

function onNodeClick(event: any) {
    // event.node.id is saved in store
    graphStore.activeNodeId = event.node.id
    isSidebarOpen.value = true
}

function onPaneClick() {
    isSidebarOpen.value = false
    graphStore.clearActiveNode()
}

function validateEdges(connection: any) {

    // find target and source nodes
    const sourceNode = flowNodes.value.find((node: any) => node.id === connection.source)
    const targetNode = flowNodes.value.find((node: any) => node.id === connection.target)
    // check if they exist
    if (sourceNode) {

        if (sourceNode.type === 'float') {
            return false
        }
        if (sourceNode.type === 'integer') {
            return false
        }
    }
    return true
}

function testXML() {

    const xmlResult = graphStore.exportGraphToXML()

    console.log("XML TEXT")
    console.log(xmlResult)
}

</script>

<template>
    <div style="height: 100vh; width: 100%; display: flex; flex-direction: column;">
        <VueFlow 
        :nodes="graphStore.nodes" 
        :edges="graphStore.edges" 
        :node-types="myNodeTypes" 
        connection-mode="strict"
        :is-valid-connection="validateEdges" 
        :default-edge-options="{ type: 'smoothstep', animated: false }"
        @node-click="onNodeClick"
        @pane-click="onPaneClick">
            <Panel position="top-right" class="custom-center-panel">
                <Toolbar />
            </Panel>
        </VueFlow>

        <Sidebar :is-open="isSidebarOpen" @close="isSidebarOpen = false"
            @open-category-table="isCategoryTableOpen = true" />

        <Category :is-open="isCategoryTableOpen" @close="isCategoryTableOpen = false" />

        <button @click="testXML">show xml in console</button>

       
    </div>
    <CodeOutput :is-open="isCodeWindowOpen" @close="isCodeWindowOpen = false" :code="wflCode"/>
</template>

<style>
.custom-center-panel {
    position: absolute;
    top: 20px;
    left: 0;
    right: 0;
    width: 100%;
    transform: none;
    margin: 0;
    z-index: 50;
}

.vue-flow-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
}

</style>
