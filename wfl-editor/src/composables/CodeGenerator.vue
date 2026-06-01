<script lang="ts">
import { ref } from 'vue'
import type { Node, Edge } from '@vue-flow/core'

const props = defineProps<{
    nodes: Node[]
    edges: Edge[]
}>()

const generatedCode = ref('')
const isModalOpen = ref(false)

function generateWflCode() {
    const rawNodes = props.nodes
    const rawEdges = props.edges

}
</script>