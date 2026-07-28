import Plotly from 'plotly.js-dist-min'

export function renderHypImp(element: HTMLElement, result: { "importances": Record<string, number> }) {

    if (Object.keys(result.importances).length === 0) {
        Plotly.purge(element)
        return
    }

    const importances = result["importances"]
    const labels = Object.keys(importances)
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

    Plotly.react(element, data, layout)
}