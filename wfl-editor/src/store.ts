import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export const useGraphStore = defineStore('graph', () => {

    // define states
    const nodes: any = ref([])
    const edges: any = ref([])
    const activeNodeId = ref<string | null>(null)


    interface DescendantNode {
    node: Node
    children: DescendantNode[]
    }

    
    // for createNode to map the types to the xml export function
    const waffleSuperMap: Record<string, string> = {
        float: 'FloatHyperparameter',
        integer: 'IntegerHyperparameter',
        nominal: 'NominalHyperparameter',
        ordinal: 'OrdinalHyperparameter',
        category: 'Category'
    }

    // find an active/ currently updated node
    const activeNode = computed(() => {
        return nodes.value.find((n: any) => n.id === activeNodeId.value) || null
    })

    // maps node types to their XML tag names (used in data.super for export)
    function createNode(nodeConfig: { type: string, label: string }) {

        const id = Date.now().toString()
        const categories = nodeConfig.type === 'nominal' || nodeConfig.type === 'ordinal' ? [] : undefined
        const node = ({
            id: id,
            type: nodeConfig.type,
            position: { x: Math.random() * 500, y: Math.random() * 500 },
            data: {
                label: nodeConfig.label,
                name: '',
                super: waffleSuperMap[nodeConfig.type],
                constraints: { lower: null, upper: null, default: null, level: 0 },
                categories: categories ? [] : undefined,
                children: categories ? [] : undefined,
                 customConstraints: []
            }
        })
        nodes.value.push(node)
        return node
    }

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

        if (parentId) {
            if (!parentNode.data.childrenIds) parentNode.data.childrenIds = []
            if (!parentNode.data.childrenIds.includes(childId)) {
                parentNode.data.childrenIds.push(childId)
            }
        }
    }

    function getAllDescendants(nodeId:string): Node[] {
        const node = nodes.value.find((n: Node) => n.id === nodeId)
        if(!node) return []

         const directChildren = (node.data?.childrenIds || [])
        .map((id: string) => nodes.value.find((n: any) => n.id === id))
        .filter(Boolean)

        const nestedDescendants = directChildren.flatMap((child: any) => getAllDescendants(child.id))

        return [...directChildren, ...nestedDescendants]
    }
    // collect all children and categories of the parent node
    const getCategoryItem = computed(() => {
        if (!activeNodeId.value) return []
        return getAllDescendants(activeNodeId.value)
    })


    //create category node 
    function createCategoryBox(sourceNode: Node, targetNode: Node) {
        const id = Date.now().toString()
         const midX = (sourceNode.position.x + targetNode.position.x) / 2
    const midY = (sourceNode.position.y + targetNode.position.y) / 2 

          const node = {
        id,
        type: 'category',
        position: { x: midX, y: midY },
        // for xml export
        data: { name: '', super: waffleSuperMap['category'] }
    }
    nodes.value.push(node)
    return node
    }

    // extract the data and make it xml
    function exportGraphToXML() {
        const xmlDoc = document.implementation.createDocument(null, 'SearchSpace', null);
        const root = xmlDoc.documentElement;

        const getChildrenForCategory = (parentId: string, categoryName: string) => {
            return nodes.value.filter((child: any) => {
                const isChild = nodes.value.find((n: any) => n.id === parentId)?.data?.childrenIds?.includes(child.id);
                return isChild && child.data?.parentCategory === categoryName;
            })
        }

        const buildNodeXML = (node: any): HTMLElement => {
            const tagName = node.type ===  node.data?.super 
            const nodeEl = xmlDoc.createElement(tagName);

            nodeEl.setAttribute('name', node.data?.name || node.data?.label);
            nodeEl.setAttribute('id', node.id);

            // extract constraints and parameters
            if (node.data?.constraints) {
                const constraintsEl = xmlDoc.createElement('Constraints');
                Object.entries(node.data.constraints).forEach(([key, val]) => {
                    if (val !== null && val !== undefined && key !== 'level') {
                        const cEl = xmlDoc.createElement(key);
                        cEl.textContent = val.toString();
                        constraintsEl.appendChild(cEl);
                    }
                })
                nodeEl.appendChild(constraintsEl)
            }
            const childIds = node.data?.childrenIds || []
            childIds.forEach((childId: string) => {
            const childNode = nodes.value.find((n: any) => n.id === childId)
            if (childNode)
             {
                nodeEl.appendChild(buildNodeXML(childNode))
             }
             })

             return nodeEl
         }

        const allChildIds = new Set(nodes.value.flatMap((n: any) => n.data?.childrenIds || []))
        const rootNodes = nodes.value.filter((n: any) => !allChildIds.has(n.id))
       
        rootNodes.forEach((rootNode: any) =>
        {
            root.appendChild(buildNodeXML(rootNode));
        });
        const serializer = new XMLSerializer();
        return `<?xml version="1.0" encoding="UTF-8"?>\n${serializer.serializeToString(xmlDoc)}`;
    }

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
        getCategoryItem,
        createNode,
        exportGraphToXML,
        createCategoryBox,
        getAllDescendants
    }
})