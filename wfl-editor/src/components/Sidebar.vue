<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{
    node: any | null
    isOpen: boolean
}>()

const newCategory = ref('')

const emit = defineEmits(['close'])

const showError = ref(false)

function validateInput() {
    // TODO
}

function addCategory() {
    if (!newCategory.value.trim()) {
        showError.value = true
        return
    }
    else if (newCategory.value) {
        props.node.data.categories.push(newCategory.value)
        newCategory.value = ''
    }
}

</script>

<template>
    <div :class="['sidebar', { 'sidebar-closed': !props.isOpen }]">

        <button class="close-btn" @click="emit('close')">✕</button>

        <div v-if="props.node" class="sidebar-content">
            <h3>{{ props.node.data.label }}</h3>
            <p class="node-id">ID: {{ props.node.id }}</p>
            <hr />
            <span :class="['dot', props.node.type]"></span>
            <!-- nummerical parameters -->
            <div v-if="props.node.type === 'float' || props.node.type === 'integer'">
                <label>Name</label>
                <input v-model="props.node.data.name" class="styled-input" />

                <label>Upper</label>
                <input type="number" :step="props.node.type === 'float' ? '0.1' : '1'" v-model="props.node.data.upper"
                    class="styled-input" />

                <label>Lower</label>
                <input type="number" v-model="props.node.data.lower" class="styled-input" />

                <label>Default</label>
                <input type="number" v-model="props.node.data.default" :min="props.node.data.lower"
                    :max="props.node.data.upper" class="styled-input" />

                <label>Level</label>
                <input type="number" v-model="props.node.data.level" placeholder="0" class="styled-input" />
            </div>

            <!-- categorical parameters -->
            <div v-else-if="props.node.type === 'nominal' || props.node.type === 'ordinal'">
                <label>Name</label>
                <input type="text" v-model="props.node.data.name" class="styled-input" />

                <label>Categories</label>
                <ul>
                    <li v-for="(category, index) in props.node.data.categories" :key="index">
                        {{ category }}
                        <button @click="props.node.data.categories.splice(index, 1)">x</button>
                    </li>
                </ul>
                <input type="text" v-model="newCategory" class="styled-input" />
                <p v-if="showError" style="color: red; font-size: 12px;">Category cannot be empty</p>
                <div>
                    <button @click="addCategory()">Add
                        category</button>
                </div>
                <label>Default</label>
                <input type="number" v-model="props.node.data.default" :min="props.node.data.lower"
                    :max="props.node.data.upper" class="styled-input" />

                <label>Level</label>
                <input type="number" v-model="props.node.data.level" placeholder="0" class="styled-input" />
            </div>
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
</style>