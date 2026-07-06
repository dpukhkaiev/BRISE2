import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

export const useGraphStore = defineStore('graph', () => {

    // define states
    const nodes: any = ref([])
    const edges: any = ref([])
    const activeNodeId = ref<string | null>(null)

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
        return nodes.value.find((n: Node) => n.id === activeNodeId.value) || null
    })

    // localStorage for auto save
    watch(() => [nodes.value, edges.value],
        () => {
            localStorage.setItem('graph-state', JSON.stringify({
                nodes: nodes.value, 
                edges: edges.value,
            }))
        }, {deep: true})

    function removeFromLocalStorage() {
        nodes.value = []
        edges.value = []

        localStorage.removeItem('graph-state')
       
    }

    function loadFromLocalStorage() {
        const saved = localStorage.getItem('graph-state')
        if(!saved) {return}
        const {nodes: savedNodes, edges: savedEdges} = JSON.parse(saved)
        nodes.value = savedNodes
        edges.value = savedEdges
    }

    function createUniqueName(baseName: string): string {
        let counter = 1
        let uniqueName = `${baseName} ${counter}`
        // loop until found a name that any of the nodes have
        while (nodes.value.some((n: Node) => n.data?.name === uniqueName)) {
            counter++
            uniqueName = `${baseName} ${counter}`

        }

        return uniqueName
    }

    // maps node types to their XML tag names (used in data.super for export)
    function createNode(nodeConfig: { type: string, label: string }) {

        const id = Date.now().toString()
        const categories = nodeConfig.type === 'nominal' || nodeConfig.type === 'ordinal' ? [] : undefined
        const autoName = createUniqueName(nodeConfig.label)
        const node = ({
            id: id,
            type: nodeConfig.type,
            position: { x: Math.random() * 500, y: Math.random() * 500 },
            data: {
                label: nodeConfig.label,
                name: autoName,
                super: waffleSuperMap[nodeConfig.type],
                constraints: { lower: null, upper: null, default: null, level: 0 },
                categories: categories ? [] : undefined,
                children: categories ? [] : undefined,
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

    // check if a node already has a parent
    function hasParent(nodeId: string): boolean {
        return nodes.value.some((n:Node) => n.data?.childrenIds?.includes(nodeId))
    }

    function getParent(nodeId: string) {
       const parent = nodes.value.find((n: Node) => n.data?.childrenIds?.includes(nodeId))
        return parent
    }

    function wouldCreateCycle(targetId: string, sourceId: string): boolean {
      const child = getAllDescendants(targetId)
      const isChild = (child.some((n: Node) => n.id === sourceId))
           return isChild
    }

    // ensures unique names for hyperparameter nodes and category nodes
    function checkDuplicates(existingId: string, nodeName: string): boolean{
        if (!nodeName.trim()) return false
         const node = (nodes.value.some((n: Node) => n.id !== existingId &&  n.data.name === nodeName) )
            if(node)
                { return true }
                  else return false
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

    function getAllAncestors(nodeId:string): Node[] {
        const node = nodes.value.find((n: Node) => n.id === nodeId)
        if(!node) return []

        const directParent = getParent(nodeId)
        if(!directParent) {
            return []
        }
        const ancestors = getAllAncestors(directParent.id)

        return [directParent, ...ancestors]

      
    }

    function getAllDescendants(nodeId:string): Node[] {
        const node = nodes.value.find((n: Node) => n.id === nodeId)
        if(!node) return []

         const directChildren = (node.data?.childrenIds || [])
        .map((id: string) => nodes.value.find((n: Node) => n.id === id))
        .filter(Boolean)

        const nestedDescendants = directChildren.flatMap((child: Node) => getAllDescendants(child.id))

        return [...directChildren, ...nestedDescendants]
    }
    // collect all children and categories of the parent node
    const getCategoryItem = computed(() => {
        if (!activeNodeId.value) return []
        return getAllDescendants(activeNodeId.value)
    })

    //create category node 
    function createCategoryBox(sourceNode: Node, categoryName?: string, targetNode?: Node) {
         if (targetNode && hasParent(targetNode.id)) {
        console.warn('Target has already a parent')
        return null
     }

        const id = Date.now().toString()
      
        // position for custom categories on canvas
        let posX = sourceNode.position.x + 150
        let posY = sourceNode.position.y + 50

        if (targetNode && typeof targetNode !== 'undefined') {
            posX = (sourceNode.position.x + targetNode.position.x) / 2
            posY = (sourceNode.position.y + targetNode.position.y) / 2 
        }

        const finalName = categoryName || createUniqueName('Category')

        // flag for custom categories, if no targetNode exists then true
        const isManualCategory = !targetNode 

        const node = {
        id,
        type: 'category',
        position: { x: posX, y: posY },
        // for xml export
        data:{ 
                name: finalName, 
                super: waffleSuperMap['category'],
                childrenIds: [] ,
                isManual: isManualCategory 
        }
      }


        nodes.value.push(node)

        edges.value.push({
            id: `e-${sourceNode.id}-${id}`,
            source: sourceNode.id,
            target: id
        })

        // register custom category node as a direct child of the parent node
        if (!sourceNode.data.childrenIds) sourceNode.data.childrenIds = [];
        sourceNode.data.childrenIds.push(id)

        if(!targetNode) { return }

        edges.value.push({
            id: `e-${id}-${targetNode.id}`,
            source: id,
            target: targetNode.id
        })
        
        if (!node.data.childrenIds)    node.data.childrenIds = [];
        // register target node as child of the category node
        (node.data.childrenIds as any).push(targetNode.id)
    
        console.log('added node', node.data.childrenIds)
        return node

        }

    // delete categories custom and nested nodes 
    function removeCategory(nodeId: string, categoryName: string){
        if(!nodeId) return

        // find current selected node (of whom sidebar is shown) 
        const parentNode = nodes.value.find((n: Node) => n.id === nodeId)
        
        //search in all descendants for the id of element to be deleted
        const allDescendants = getAllDescendants(parentNode.id)
        const elementToDelete = allDescendants.find((n:Node) => n.data.name === categoryName)

        if(elementToDelete) {
            // 
            const targetId = elementToDelete.id
            // all sub nodes of the element to be deleted
        const subDescendants = getAllDescendants(targetId);
        const idsToDelete = [targetId, ...subDescendants.map((d: Node) => d.id)];

        // delete node from canvas
        nodes.value = nodes.value.filter((n: Node) => !idsToDelete.includes(n.id));

        // delete edges
        edges.value = edges.value.filter((e: Edge) => 
            !idsToDelete.includes(e.source) && !idsToDelete.includes(e.target)
        );

        // clear from the childIds array deleted elements
        nodes.value.forEach((n: Node) => {
            if (n.data?.childrenIds) {
                n.data.childrenIds = n.data.childrenIds.filter((id: string) => !idsToDelete.includes(id));
            }
        });
        
        // 
        if (parentNode.data?.childrenIds) {
            parentNode.data.childrenIds = parentNode.data.childrenIds.filter((id: string) => !idsToDelete.includes(id));
        }
     }
        }
        
  function calculateNodePath(nodeId: string): string {
    const ancestorNames = getAllAncestors(nodeId)
        .reverse()
        .map((n: Node) => n.data?.name)
    
    const node = nodes.value.find((n: Node) => n.id === nodeId)
    return ['Context', 'Searchspace', ...ancestorNames, node?.data?.name]
        .filter(Boolean)
        .join('.')
}
        

    // extract the data and make it xml
    function exportGraphToXML() {
        const xmlDoc = document.implementation.createDocument(null, 'SearchSpace', null);
        const root = xmlDoc.documentElement;

        const buildNodeXML = (node: Node): Element => {
            const tagName =  node.data?.super 
            const nodeEl = xmlDoc.createElement(tagName);

            nodeEl.setAttribute('name', node.data?.name || node.data?.label);
            nodeEl.setAttribute('id', node.id);
  const isCategorical = node.data?.super === 'NominalHyperparameter' || node.data?.super === 'OrdinalHyperparameter';
            // extract constraints and parameters for nummerical nodes
          
            if (node.data?.constraints) {
                const constraintsEl = xmlDoc.createElement('Constraints');
                   let hasConstraints = false
                   
                Object.entries(node.data.constraints).forEach(([key, val]) => {
                    if (val !== null && val !== undefined && key !== 'level' && val !== '') {
                        if (isCategorical && key === 'default') return;
                        const cEl = xmlDoc.createElement(key)
                        cEl.textContent = val.toString()
                        constraintsEl.appendChild(cEl)
                           hasConstraints = true
                    }
                })
        

            // extract default for categorical nodes
          
           if(isCategorical){
          
            const defaultEl = xmlDoc.createElement('default')
                defaultEl.textContent =  calculateNodePath(node.id)
                constraintsEl.appendChild(defaultEl)
                hasConstraints = true
                    }
                

                 if (hasConstraints) nodeEl.appendChild(constraintsEl)
            }
            const childIds = node.data?.childrenIds || []
            childIds.forEach((childId: string) => {
            const childNode = nodes.value.find((n: Node) => n.id === childId)
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

    function downloadCode(code: string, filename='searchspace.wfl', type = 'text/plain') {
        const blob = new Blob([code], { type })
        const url = URL.createObjectURL(blob)

        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()

        document.body.removeChild(link)
        URL.revokeObjectURL(url)

    }

    return {
        nodes,
        edges,
        activeNodeId,
        activeNode,
        createUniqueName,
        addNode,
        addChildToNode,
        clearActiveNode,
        getCategoryItem,
        createNode,
        exportGraphToXML,
        createCategoryBox,
        getAllDescendants,
        removeCategory,
        checkDuplicates,
        hasParent,
        downloadCode,
        loadFromLocalStorage,
        removeFromLocalStorage,
        wouldCreateCycle,
        getAllAncestors,
        calculateNodePath
    }
})