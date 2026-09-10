<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../store.ts'
import type { Node } from '@vue-flow/core'

const props = defineProps<{
    isOpen: boolean
    viewMode: 'categories' | 'nodes' | null
}>()

const emit = defineEmits(['close', 'isOpen'])
const graphStore = useGraphStore()



const activeNode = computed(() => graphStore.activeNode as any)

// all children of the parent node (direct and nested)
const connectedChildren = computed(() => {
    if (!activeNode.value.id) return []
    const descendants = graphStore.getAllDescendants(activeNode.value.id)
    return descendants
        .filter((c: any) => !c.data?.isManual)
        .map((c: any) => c.data?.name || c.data?.label);
})

// manually created categories
const customCategories = computed(() => {
    if (!activeNode.value?.id) return []
    return graphStore.nodes
        .filter((node: Node) =>
            node.type === 'category' &&
            node.data?.isManual &&
            graphStore.edges.some((e: any) => e.source === activeNode.value.id && e.target === node.id)
        )
        .map((node: any) => node.data?.name)
});

</script>

<template>
    <div v-if="props.isOpen && props.viewMode === 'categories'" class="category-overlay">
        <div class="category-modal">
            <button class="cat-btn" @click="emit('close')">x</button>
            <h3>All Categories</h3>
            <ul>
                <li v-for="(cat, index) in customCategories" :key="index">
                    {{ cat }}
                </li>
            </ul>
        </div>
    </div>
    <div v-if="props.isOpen && props.viewMode === 'nodes'" class="category-overlay">

        <div class="children-modal">
            <button class="cat-btn" @click="emit('close')">x</button>
            <h3>All Dependent Parameters</h3>
            <ul>
                <li v-for="(cat, index) in connectedChildren" :key="index">
                    {{ cat }}
                </li>
            </ul>
        </div>
    </div>



</template>

<style scoped>
.category-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 200;
    display: flex;
    align-items: center;
    justify-content: center;
}

.category-modal {
    background: white;
    padding: 20px;
    border-radius: 8px;
    min-width: 300px;
}

.children-modal {
    background: white;
    padding: 20px;
    border-radius: 8px;
    min-width: 300px;
}

.btn-cat {
    background-color: #40E0D0;
}
</style>