import { createPinia, setActivePinia } from "pinia"

import { useMainEventStore } from "../entities/main"
import type { PlotlyInstance } from "../widgets/charts/model/chart.types"

// Loads the app's own modular Plotly build (the same traces the real app registers),
// so benchmarks measure against exactly what production renders with.
export async function loadBenchmarkPlotly(): Promise<PlotlyInstance> {
    setActivePinia(createPinia())

    const store = useMainEventStore()

    await store.loadPlotly()

    if (!store.plotlyInstance) {
        throw new Error("Plotly failed to load")
    }

    return store.plotlyInstance
}
