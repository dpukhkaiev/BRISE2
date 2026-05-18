<script setup lang="ts">

const props = defineProps<{
    node: any | null
    isOpen: boolean
}>()

const emit = defineEmits(['close'])
</script>

<template>
    <div :class="['sidebar', { 'sidebar-closed': !props.isOpen }]">

        <button class="close-btn" @click="emit('close')">✕</button>

        <div v-if="props.node" class="sidebar-content">
            <h3>{{ props.node.data.label }}</h3>
            <p class="node-id">ID: {{ props.node.id }}</p>
            <hr />

            <!-- nummerical parameters -->
            <div v-if="props.node.type === 'float' || props.node.type === 'integer'">
                <label>Name</label>
                <input type="text" v-model="props.node.data.value" class="styled-input" />
            </div>

            <!-- categorical parameters -->
            <div v-else-if="props.node.type === 'nominal' || props.node.type === 'ordinal'">
                <label>Name</label>
                <input type="text" v-model="props.node.data.value" class="styled-input" />
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

.styled-input,
.styled-select {
    width: 100%;
    padding: 8px;
    margin-top: 6px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}
</style>