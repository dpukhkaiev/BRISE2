/*import Plotly from 'plotly.js-dist-min'
import type { Data } from 'plotly.js'
import type { Solution } from '../../../entities/task/model/task-data.model'

interface RenderOptions {
    result: Map<string, any>
    measPoints: Array<[any, any]>
    solution?: Solution
    x: any[]
    y: any[]
    theme: {
        type: string
        color: string
        smooth: string | boolean
    }
    xLabel: string
    yLabel: string
}

declare const scheduler: {
    yield(): Promise<void>
}

const data = [] as Data[]

async function zParser(
    result: Map<string, any>,
    x: any[],
    y: any[]
): Promise<any[][]> {
    const z: any[][] = []

    for (const yVal of y) {
        const row = []

        for (const xVal of x) {
            const value = result.get(String([yVal, xVal]))
            row.push(value && value[0])
        }

        z.push(row)

        if ("scheduler" in window && typeof scheduler.yield === "function") {
            await scheduler.yield()
        }
    }

    return z
}

export async function renderHeatmap(
    element: HTMLElement,
    options: RenderOptions
) {
    const z = await zParser(options.result, options.x, options.y)

    const data = [
        {
            z,
            x: options.x.map(String),
            y: options.y.map(String),
            type: options.theme.type,
            colorscale: options.theme.color,
            zsmooth: options.theme.smooth
        },
        {
            type: "scatter",
            mode: "markers",
            marker: {
                color: "grey",
                size: 7,
                symbol: "cross"
            },
            x: options.measPoints.map(p => p[1]),
            y: options.measPoints.map(p => p[0])
        },
        {
            type: "scatter",
            mode: "markers",
            marker: {
                color: "gold",
                size: 16,
                symbol: "star"
            },
            showlegend: false,
            hoverinfo: "none",
            x: options.solution && [options.solution.configurations[1]],
            y: options.solution && [options.solution.configurations[0]]
        }
    ]

    const layout = {
        margin: { l: 220 },
        title: { text: "Heat Map Results" },
        autosize: true,
        showlegend: false,
        xaxis: {
            title: options.xLabel,
            type: "category",
            categoryorder: "array",
            categoryarray: options.x,
            range: [-0.5, options.x.length - 0.5]
        },
        yaxis: {
            title: options.yLabel,
            type: "category",
            categoryorder: "array",
            categoryarray: options.y,
            range: [-0.5, options.y.length - 0.5]
        }
    }

    Plotly.react(element, data, layout)
}*/