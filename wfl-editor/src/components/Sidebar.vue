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

    // create a custom category
    graphStore.createCategoryBox(activeNode.value, newCategory.value)
    newCategory.value = ''
}

const ancestors = computed(() => {
    if (!activeNode.value?.id) return ''
    const ancestorNames = graphStore.getAllAncestors(activeNode.value.id).reverse().map((n: Node) => n.data?.name)

    const fullPath = ['Context', 'Searchspace', ancestorNames, activeNode.value.data.name].join('.')
    return fullPath
})


// all children of the parent node (direct and nested)
const connectedChildren = computed(() => {
    if (!activeNode.value.id) return []
    const descendants = graphStore.getAllDescendants(activeNode.value.id)
    return descendants
        .filter((c: Node) => !c.data?.childrenIds)
        .map((c: Node) => c.data?.name || c.data?.label);
})

// manually created categories
const categories = computed(() => {
    if (!activeNode.value?.id) return []
    return graphStore.nodes
        .filter((node: Node) =>
            node.type === 'category' &&
            graphStore.edges.some((e: any) => e.source === activeNode.value.id && e.target === node.id)
        )
        .map((node: any) => node.data?.name)
});

// block sidebar from closing 
function blockSidebar() {
    if (!activeNode.value?.data.name || isNodeNameTaken.value || isConstraintsInvalid.value) {
        return
    }
    emit('close')
}

function removeChild(categoryName: string) {
    if (activeNode.value?.id) {
        graphStore.removeCategory(activeNode.value.id, categoryName)
    }
}


const isNameTaken = computed(() => {
    if (!activeNode.value?.id || !newCategory.value) return false
    const names = graphStore.checkDuplicates(activeNode.value.id, newCategory.value)
    if (names) {
        return true
    } else return false
})

const isNodeNameTaken = computed(() => {
    const name = graphStore.checkDuplicates(activeNode.value.id, activeNode.value.data.name)
    if (name) { return true } else return false
})

const isConstraintsInvalid = computed(() => {
    const lower = activeNode.value?.data?.constraints?.lower
    const upper = activeNode.value?.data?.constraints?.upper

    if (lower === null || upper === null || lower === undefined || upper === undefined || lower === '' || upper === '') {
        return false
    }

    return Number(lower) > Number(upper)
})

const isDefaultInvalid = computed(() => {
    const lower = activeNode.value?.data?.constraints?.lower
    const upper = activeNode.value?.data?.constraints?.upper
    const d = activeNode.value?.data?.constraints?.default

    if (d === undefined || d === '' || d === null) { return false }
    return Number(d) < Number(lower) || Number(d) > Number(upper)
})


// validate name when changed
const updateName = computed({
    get() {
        return activeNode.value?.data?.name || ''
    },
    set(newValue: string) {
        if (activeNode.value?.id) {
            graphStore.updateNodeName(activeNode.value.id, newValue)
        }
    }
})

const directCategories = computed(() => {
    if (!activeNode.value?.id) return []
    return graphStore.getDirectCategories(activeNode.value.id)
})

const defaultCategoryId = computed({
    get() {
        return activeNode.value?.data?.defaultPathId || ''
    },
    set(categoryId: string) {
        if (activeNode.value?.id) {
            graphStore.setDefault(activeNode.value.id, categoryId)
        }
    }
})

</script>

<template>
    <div :class="['sidebar', { 'sidebar-closed': !props.isOpen }]">

        <button class="close-btn" @click="blockSidebar">✕</button>

        <div v-if="activeNode" class="sidebar-content">
            <h3>{{ activeNode.data.name || activeNode.data.label }}</h3>
            <p class="node-id">ID: {{ graphStore.activeNodeId }}</p>
            <hr />
            <span :class="['dot', activeNode?.type]"></span>
            <!-- nummerical parameters -->
            <div v-if="activeNode?.type === 'float' || activeNode?.type === 'integer'">
                <label>Name</label>
                <input v-model="updateName" class="styled-input"
                    :class="{ 'input-error': !updateName || isNodeNameTaken }" />

                <p v-if="!activeNode.data.name" style="color: red; font-size: 12px; margin-top: 4px;">
                    name is required
                </p>
                <p v-if="isNodeNameTaken" style="color: red; font-size: 12px;">That name is
                    already in use! </p>

                <label>Upper</label>
                <input type="number" :step="activeNode?.type === 'float' ? '0.1' : '1'"
                    v-model="activeNode.data.constraints.upper" class="styled-input"
                    :class="{ 'input-error': isConstraintsInvalid }" />

                <label>Lower</label>
                <input type="number" v-model="activeNode.data.constraints.lower"
                    :step="activeNode?.type === 'float' ? '0.1' : '1'" class="styled-input"
                    :class="{ 'input-error': isConstraintsInvalid }" />

                <p v-if="isConstraintsInvalid" style="color: red; font-size: 12px; margin-top: 4px;">
                    Lower bound cannot be greater than Upper bound!
                </p>


                <label>Default</label>
                <input type="number" v-model="activeNode.data.constraints.default" :min="activeNode?.data.lower"
                    :max="activeNode?.data.upper" class="styled-input" />
                <p v-if="isDefaultInvalid" style="color: red; font-size: 12px; margin-top: 4px;">
                    Default cannot be greater than Upper and lower than Lower
                </p>
                <label>Level</label>
                <div>
                    <span> {{ activeNode.data?.level }} </span>
                </div>
            </div>

            <!-- categorical parameters -->
            <div v-else-if="activeNode?.type === 'nominal' || activeNode?.type === 'ordinal'">
                <label>Name</label>
                <input type="text" v-model="updateName" class="styled-input"
                    :class="{ 'input-error': !updateName || isNodeNameTaken }" />

                <p v-if="!activeNode.data.name" style="color: red; font-size: 12px; margin-top: 4px;">
                    name is required
                </p>
                <p v-if="isNodeNameTaken" style="color: red; font-size: 12px;">That name is
                    already in use! </p>
                <!--custom categories-->
                <label>Categories</label>
                <ul>

                    <li v-for="(item, index) in categories.slice(0, 5)" :key="index">
                        {{ item }}
                        <button class="btn btn-danger" @click="removeChild(item)">x</button>
                    </li>

                    <div v-if="categories.length > 5">
                        <button type="button" class="btn-link" @click="emit('open-category-table', 'categories')">
                            + {{ categories.length - 5 }} ↗
                        </button>
                    </div>
                </ul>

                <input type="text" v-model="newCategory" @input="showError = false" class="styled-input"
                    :class="{ 'input-error': isNameTaken }" />
                <p v-if="showError" style="color: red; font-size: 12px;">Category cannot be empty</p>
                <p v-if="isNameTaken" style="color: red; font-size: 12px;">That name is
                    already in use! </p>
                <div>
                    <button class="btn btn-primary" @click="addCategory()" :disabled="isNameTaken ||
                        !newCategory.trim()">Add
                        category</button>
                </div>


                <label>Dependent Parameters</label>
                <ul>

                    <li v-for="(item, index) in connectedChildren.slice(0, 5)" :key="index">
                        {{ item }}
                        <button class="btn btn-danger" @click="removeChild(item)">x</button>
                    </li>

                    <div v-if="connectedChildren.length > 5">
                        <button type="button" class="btn-link" @click="emit('open-category-table', 'nodes')">
                            + {{ connectedChildren.length - 5 }} ↗
                        </button>
                    </div>
                </ul>

                <label>Default</label>

                <select v-model="defaultCategoryId" class="styled-select">

                    <option value="">No category selected</option>
                    <option v-for="cat in directCategories" :key="cat.id" :value="cat.id">
                        {{ cat.data.name }}
                    </option>

                </select>

                <label>Level</label>
                <div>
                    <span> {{ activeNode.data.level }} </span>
                </div>
            </div>

            <div v-if="activeNode?.type === 'category'">
                <label>Dependent Parameters</label>
                <ul>

                    <li v-for="(item, index) in connectedChildren.slice(0, 5)" :key="index">
                        {{ item }}
                        <button class="btn btn-danger" @click="removeChild(item)">x</button>
                    </li>

                    <div v-if="connectedChildren.length > 5">
                        <button type="button" class="btn-link" @click="emit('open-category-table', 'nodes')">
                            + {{ connectedChildren.length - 5 }} ↗
                        </button>
                    </div>
                </ul>
            </div>



        </div>

        <div v-if="activeNode?.type === 'category'" style="padding: 8px 16px;">
            <label>Name</label>
            <input type=" text" v-model="updateName" class="styled-input"
                :class="{ 'input-error': !updateName || isNodeNameTaken }" />

            <p v-if="!activeNode.data.name" style="color: red; font-size: 12px; margin-top: 4px;">
                name is required
            </p>
            <p v-if="isNodeNameTaken" style="color: red; font-size: 12px;">That name is
                already in use! </p>

        </div>

    </div>
</template>

<style scoped>
.sidebar {
    position: absolute;
    right: 0;
    top: 0;
    height: 100%;
    width: 400px;
    background-color: #ffffff;
    box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
    transition: transform 0.25s ease-out;
    z-index: 100;
    border-left: 1px solid #e2e8f0;
    color: #1e293b;

}

.sidebar-closed {
    transform: translateX(100%);
    visibility: hidden;
}

.sidebar-content {
    padding: 20px;
    margin-top: 20px;
}

.def {
    font-size: 16px;
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
    font-size: 16px;
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

.btn-primary:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
    border-color: #cbd5e1;
    cursor: not-allowed;
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