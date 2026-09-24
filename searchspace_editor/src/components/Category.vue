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

// manually created categories, in childrenIds order
const customCategories = computed<Node[]>(() => {
    if (!activeNode.value?.id) return []
    return graphStore.getDirectCategories(activeNode.value.id)
        .filter((node: Node) => node.data?.isManual)
});

</script>

<template>
    <div v-if="props.isOpen && props.viewMode === 'categories'" class="category-overlay">
        <div class="category-modal">
            <button class="cat-btn" @click="emit('close')">x</button>
            <h3>All Categories</h3>
            <ul>
                <li v-for="(cat, index) in customCategories" :key="cat.id">
                    <span class="cat-name">{{ cat.data?.name }}</span>
                    <span class="cat-actions">
                        <button class="btn btn-move" :disabled="index === 0"
                            @click="graphStore.moveCategory(activeNode.id, cat.id, 'up')" title="Move up">▲</button>
                        <button class="btn btn-move" :disabled="index === customCategories.length - 1"
                            @click="graphStore.moveCategory(activeNode.id, cat.id, 'down')" title="Move down">▼</button>
                    </span>
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

ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
}

li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 16px;
}

.cat-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.cat-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
}

.btn-move {
    background-color: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    padding: 2px 6px;
    font-size: 11px;
    line-height: 1;
    border-radius: 4px;
    cursor: pointer;
}

.btn-move:hover:not(:disabled) {
    background-color: #e2e8f0;
}

.btn-move:disabled {
    opacity: 0.35;
    cursor: not-allowed;
}
</style>