<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../store.ts'


const props = defineProps<{
    isOpen: boolean
}>()

const emit = defineEmits(['close', 'isOpen'])
const graphStore = useGraphStore()


const activeNode = computed(() => graphStore.activeNode as any)


const connectedChildren = computed(() => {
    const children = activeNode.value?.data.childrenIds || []
    return children
        .map((id: string) => graphStore.nodes.find((n: any) => n.id === id))
        .filter(Boolean) // filter null/undefined for the case if nodes deleted
})



const allCategories = computed(() => {
    const manual = activeNode.value?.data.categories || [];
    const children = connectedChildren.value.map((c: any) => c.data.name);
    return [...manual, ...children];
});


</script>

<template>
    <div v-if="props.isOpen" class="category-overlay">
        <div class="category-modal">
            <button class="cat-btn" @click="emit('close')">x</button>
            <h3>All Categories</h3>
            <ul>
                <li v-for="(cat, index) in allCategories" :key="index">
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

.btn-cat {
    background-color: #40E0D0;
}
</style>