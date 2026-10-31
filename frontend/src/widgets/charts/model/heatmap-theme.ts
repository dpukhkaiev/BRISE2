import { ref } from 'vue'
import { Color, PlotType, Smooth } from './chart.types'

// Single shared instance so Heatmap and HeatmapReg colorscales stay in sync.
export const theme = ref({
    type: PlotType[0] as string,
    color: Color[0] as string,
    smooth: Smooth[0] as string | boolean
})
