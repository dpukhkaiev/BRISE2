import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface PointExp {
    configurations: Array<any>;
    results: Array<any>;
    time: any;
    'measured points': number;
}

export const usePlotStore = defineStore('plots', () => {
    const selected = ref({
        optHist: false,
        paraCoord : false,
        rank : false,
        hypImp : false,
        slice : false,
        contour : false,
        paretoFront : false,
        edf : false,
        intVal : false,
        termImpr : false,
        timeline : false
    })
    
    const visibleCharts = ref<string[]>([])

    const bestRes = ref<PointExp[]>([])
    const allRes = ref<PointExp[]>([])
    
    return {
        selected,
        visibleCharts,
        bestRes,
        allRes
    }
})