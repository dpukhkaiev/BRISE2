import Plotly from 'plotly.js-dist-min'

export function renderHypImp(element: HTMLElement) {
    console.log("rendering hypImp")
    const labels = ['p1', 'p2']
    const values = [0.9, 0.1]

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