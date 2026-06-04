<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGraphStore } from '../store.ts'
import { storeToRefs } from 'pinia'
import type { Node } from '@vue-flow/core'


const graphStore = useGraphStore()

const { activeNodeId } = storeToRefs(graphStore)
const activeNode = computed(() => graphStore.activeNode as any)

// for expanding table 
const isVisible = ref(false)


</script>

<template>
    <div :class="['category', { 'category-closed': !isVisible }]">

    </div>
</template>

<style></style>