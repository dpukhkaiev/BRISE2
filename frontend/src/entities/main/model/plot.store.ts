import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface PointExp {
    configurations: Record<string, any>;
    results: Record<string, any>;
    time: string;
    "measured points": number;
}

export const usePlotStore = defineStore('plots', () => {
    const selected = ref({
        "Optimization History": false,
        "Parallel Coordinates": false,
        "Rank Plot": false,
        "Hyperparameter Importances": false,
        "Slice Plot": false,
        "Contour Plot": false,
        "Pareto Front": false,
        "EDF Plot": false,
        "Heatmap": false,
        // "Heatmap Reg": false, // disabled, see the HeatmapReg import comment in App.vue
    })
    
    const visibleCharts = ref<string[]>([])

    const allRes = ref<PointExp[]>([])

    const canChangeVisibleCharts = ref(false)

    // final configuration suggested by BRISE
    const solution = ref<PointExp | null>(null)
    
    return {
        selected,
        visibleCharts,
        allRes,
        canChangeVisibleCharts,
        solution
    }
})