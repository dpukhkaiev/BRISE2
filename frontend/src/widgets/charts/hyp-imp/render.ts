import type { PlotlyInstance } from '../model/chart.types'
import { cleanIdentifier } from "../../../shared/lib";

export function renderHypImp(plotly: PlotlyInstance, element: HTMLElement, result: { "importances": Record<string, number> } | Record<string, never>) {

    if (result.importances == undefined || Object.keys(result.importances).length === 0) {
        plotly.purge(element)
        return
    }

    const importances = result["importances"]
    const labels = Object.keys(importances).map(cleanIdentifier)
    const values = Object.values(importances)
    const data = [
        {
            x: labels,
            y: values,
            type: 'bar' as const
        }
    ]

    const layout = {
        title: {
            text: 'Hyperparameter Importances'
        },
        autosize: true,
        xaxis: {
            title: {
                text: 'Hyperparameters'
            }
        },

        yaxis: {
            title: {
                text: 'Importance'
            },
            range: [0, 1]
        }
    }

    plotly.react(element, data, layout)
}