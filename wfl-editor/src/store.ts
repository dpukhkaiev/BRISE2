import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export const useGraphStore = defineStore('graph', () => {

    // define states
    const nodes: any = ref([])
    const edges: any = ref([])
    const activeNodeId = ref<string | null>(null)

    // find an active/ currently updated node
    const activeNode = computed(() => {
        return nodes.value.find((n: any) => n.id === activeNodeId.value) || null
    })

    // actions to change the data
    function addNode(newNode: Node) {
        nodes.value.push(newNode)
    }

    function addCategoryToNode(nodeId: string | null, categoryName: string) {
        if (!nodeId) return
        const node = nodes.value.find((n: any) => n.id === nodeId)
        if (node) {
            if (!node.data) node.data = {}
            if (!node.data.categories) node.data.categories = []

            node.data.categories.push(categoryName)
        }
    }

    function setNodes(newNodes: Node[]) {
        nodes.value = newNodes
    }

    function setEdges(newEdges: Edge[]) {
        edges.value = newEdges
    }

    return {
        nodes,
        edges,
        activeNodeId,
        activeNode,
        addNode,
        addCategoryToNode,
        setNodes,
        setEdges
    }
})