import Plotly from 'plotly.js-dist-min'

export function renderHypImp(element: HTMLElement, result: Record<string, number>) {
    console.log("rendering hypImp. Result: ", result)
    const labels = Object.keys(result)
    const values = Object.values(result) 

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