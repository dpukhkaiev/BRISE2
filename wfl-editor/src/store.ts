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

    // reset activeNode
    function clearActiveNode() {
        activeNodeId.value = null
    }

    // find current node and add category to it
    function addCategoryToNode(nodeId: string | null, categoryName: string) {
        if (!nodeId) return
        const node = nodes.value.find((n: any) => n.id === nodeId)
        if (node) {
            if (!node.data) node.data = {}
            if (!node.data.categories) node.data.categories = []

            node.data.categories.push(categoryName)
        }
    }

    // preserve children (so the update in newNodes in VueFlow state does not overwrite the children of the node)
    function setNodes(newNodes: Node[]) {
        nodes.value = newNodes.map((newNode) => {
            const existing = nodes.value.find((n: any) => n.id === newNode.id)
            if (existing?.data?.children) {
                newNode.data.children = existing.data.children
            }
            return newNode
        })
    }

    function setEdges(newEdges: Edge[]) {
        edges.value = newEdges
    }

    // store childId which of connected properties of a parent node
    function addChildToNode(parentId: string, childId: string) {
        const parentNode = nodes.value.find((n: any) => n.id === parentId)

        if (parent) {
            if (!parentNode.data.childrenIds) parentNode.data.childrenIds = []
            if (!parentNode.data.childrenIds.includes(childId)) {
                parentNode.data.childrenIds.push(childId)
            }
        }
    }

    // collect all children and categories of the parent node
    const getCategoryItem = computed(() => {
        const node = activeNode.value
        if (!node) return []

        const cats = node.data.categories || []
        const children = (node.data.childrenIds || []).map((id: string) => nodes.value.find((n: any) => n.id === id)?.data.name)
        return [...cats, ...children]
    })


    return {
        nodes,
        edges,
        activeNodeId,
        activeNode,
        addNode,
        addCategoryToNode,
        setNodes,
        setEdges,
        addChildToNode,
        clearActiveNode,
        getCategoryItem
    }
})