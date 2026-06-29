<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../store.ts'
import { storeToRefs } from 'pinia'
import type { Node } from '@vue-flow/core'

const props = defineProps<{
    isOpen: boolean
}>()

const graphStore = useGraphStore()

const activeNode = computed(() => graphStore.activeNode as any)

const newCategory = ref('')

const emit = defineEmits(['close', 'open-category-table'])

const showError = ref(false)

function addCategory() {
    if (!newCategory.value.trim()) {
        showError.value = true
        return
    }
    showError.value = false

    if (!activeNode.value.id) return

    // graphStore.addCategoryToNode(activeNode.value.id, newCategory.value)

    graphStore.createCategoryBox(activeNode.value, newCategory.value)
    newCategory.value = ''
}

const connectedChildren = computed(() => {
    if (!activeNode.value.id) return []
    return graphStore.getAllDescendants(activeNode.value.id)
})

function removeChild(categoryName: string) {
    if (activeNode.value?.id) {
        graphStore.removeCategory(activeNode.value.id, categoryName)
    }
}

const allCategories = computed(() => {
    const manual = activeNode.value?.data.categories || [];
    const children = connectedChildren.value.map((c: any) => c.data.name);
    return [...manual, ...children];
});

</script>

<template>
    <div :class="['sidebar', { 'sidebar-closed': !props.isOpen }]">

        <button class="close-btn" @click="emit('close')">✕</button>

        <div v-if="activeNode" class="sidebar-content">
            <h3>{{ activeNode.data.name || activeNode.data.label }}</h3>
            <p class="node-id">ID: {{ graphStore.activeNodeId }}</p>
            <hr />
            <span :class="['dot', activeNode?.type]"></span>
            <!-- nummerical parameters -->
            <div v-if="activeNode?.type === 'float' || activeNode?.type === 'integer'">
                <label>Name</label>
                <input v-model="activeNode.data.name" class="styled-input"
                    :class="{ 'input-error': !activeNode.data.name }" />

                <p v-if="!activeNode.data.name" style="color: red; font-size: 12px; margin-top: 4px;">
                    name is a required
                </p>

                <label>Upper</label>
                <input type="number" :step="activeNode?.type === 'float' ? '0.1' : '1'"
                    v-model="activeNode.data.constraints.upper" class="styled-input" />

                <label>Lower</label>
                <input type="number" v-model="activeNode.data.constraints.lower" class="styled-input" />

                <label>Default</label>
                <input type="number" v-model="activeNode.data.constraints.default" :min="activeNode?.data.lower"
                    :max="activeNode?.data.upper" class="styled-input" />

                <label>Level</label>
                <input type="number" v-model="activeNode.data.level" placeholder="0" class="styled-input" />
            </div>

            <!-- categorical parameters -->
            <div v-else-if="activeNode?.type === 'nominal' || activeNode?.type === 'ordinal'">
                <label>Name</label>
                <input type="text" v-model="activeNode.data.name" class="styled-input"
                    :class="{ 'input-error': !activeNode.data.name }" />

                <p v-if="!activeNode.data.name" style="color: red; font-size: 12px; margin-top: 4px;">
                    name is a required
                </p>

                <label>Categories</label>
                <ul>

                    <li v-for="(item, index) in allCategories.slice(0, 5)" :key="index">
                        {{ item }}
                        <button class="btn btn-danger" @click="removeChild(item)">x</button>
                    </li>

                    <div v-if="allCategories.length > 5">
                        <button type="button" class="btn-link" @click="emit('open-category-table')">
                            + {{ allCategories.length - 5 }} ↗
                        </button>
                    </div>
                </ul>


                <!--custom categories-->
                <input type="text" v-model="newCategory" @input="showError = false" class="styled-input" />
                <p v-if="showError" style="color: red; font-size: 12px;">Category cannot be empty</p>
                <div>
                    <button class="btn btn-primary" @click="addCategory()">Add
                        category</button>
                </div>

                <label>Default</label>
                <input type="number" v-model="activeNode.data.default" :min="activeNode?.data.lower"
                    :max="activeNode?.data.upper" class="styled-input" />

                <label>Level</label>
                <input type="number" v-model="activeNode.data.level" placeholder="0" class="styled-input" />

            </div>

            <!-- <label>Children</label>
            <div v-for="(c, i) in activeNode.data.category" :key="i">
                <input v-model="activeNode.data.customConstraints[i]" class="styled-input" />
                <button class="btn" @click="activeNode.data.customConstraints.splice(i, 1)">x</button>
            </div> -->

        </div>

        <div v-else class="sidebar-content">
            <p>Click on a node to configure the sidebar</p>
        </div>
    </div>
</template>

<style scoped>
.sidebar {
    position: absolute;
    right: 0;
    top: 0;
    height: 100%;
    width: 300px;
    background-color: #ffffff;
    box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
    transition: transform 0.25s ease-out;
    z-index: 100;
    border-left: 1px solid #e2e8f0;
    color: #1e293b;
}

.sidebar-closed {
    transform: translateX(100%);
}

.sidebar-content {
    padding: 20px;
    margin-top: 20px;
}

.sidebar-content ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
}

.sidebar-content li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.close-btn {
    position: absolute;
    top: 15px;
    left: 15px;
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    color: #64748b;
}

.node-id {
    font-size: 11px;
    color: #64748b;
    font-family: monospace;
}

.styled-input.input-error {
    border-color: #ef4444;
    background-color: #fef2f2;
}

.dot {
    width: 15px;
    height: 15px;
    border-radius: 50%;
    display: inline-block;
}

.dot.float {
    background-color: #9a3412;
}

.dot.integer {
    background-color: #0369a1;
}

.dot.nominal {
    background-color: #166534;
}

.dot.ordinal {
    background-color: #854d0e;
    border-color: #ca8a04
}

.styled-input,
.styled-select {
    width: 100%;
    padding: 8px;
    margin-top: 6px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}

.btn {
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    background-color: #f8fafc;
    color: #475569;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
}


.btn-primary {
    background-color: #0f172a;
    color: white;
    border: none;
    width: 100%;
    margin-top: 10px;
}

.btn-primary:hover {
    background-color: #334155;
}


.btn-danger {
    background-color: #fee2e2;
    color: #b91c1c;
    border: none;
    padding: 2px 8px;
    font-size: 12px;
    border-radius: 4px;
}

.btn-danger:hover {
    background-color: #fecaca;
}


.btn-link {
    background: none;
    border: none;
    color: #2563eb;
    font-size: 13px;
    cursor: pointer;
    text-decoration: underline;
}

.btn-link:hover {
    color: #1d4ed8;
}
</style>