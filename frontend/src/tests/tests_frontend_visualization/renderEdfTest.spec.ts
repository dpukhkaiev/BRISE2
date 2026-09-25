import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { renderEdf } from '../../widgets/charts/edf/render'
import type { PointExp } from '../../entities/main/model/plot.store'

const allRes = ref<PointExp[]>([
    {
        configurations: {
            frequency: 50,
            threads: 4
        },
        results: [123.4],
        time: '1m 20s',
        'measured points': 1
    }
])

const plotly = { react: vi.fn(), purge: vi.fn() }

describe('renderEdf', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when allRes is empty', () => {
        const element = document.createElement('div')

        const emptyAllRes = ref<PointExp[]>([])
        renderEdf(plotly, element, emptyAllRes.value)

        expect(plotly.purge).toHaveBeenCalledWith(element)
        expect(plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        const testData: PointExp[] = [
            {
                configurations: {
                    frequency: 50
                },
                results: {
                    runtime: 30
                },
                time: '1m 0s',
                'measured points': 1
            },
            {
                configurations: {
                    frequency: 60
                },
                results: {
                    runtime: 10
                },
                time: '2m 0s',
                'measured points': 2
            },
            {
                configurations: {
                    frequency: 70
                },
                results: {
                    runtime: 20
                },
                time: '3m 0s',
                'measured points': 3
            }
        ]

        renderEdf(plotly, element, testData)

        expect(plotly.react).toHaveBeenCalledTimes(1)

        const call = plotly.react.mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                x: [10, 20, 30],
                y: [1 / 3, 2 / 3, 1],
                type: 'scatter',
                mode: 'lines',
                name: 'runtime',
                line: {
                    shape: 'hv',
                    width: 2
                },
                hovertemplate:
                    `runtime: %{x}<br>` +
                    `EDF: %{y:.2f}<extra></extra>`
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderEdf(plotly, element, allRes.value)

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
            title: {
                text: "Empirical Distribution Function"
            },
            autosize: true,
            showlegend: true,
            legend: {
                title: {
                    text: "Objectives"
                }
            },
            xaxis: {
                title: {
                    text: "Objective value"
                }
            },
            yaxis: {
                title: {
                    text: "Cumulative Probability"
                },
                range: [0, 1]
            },
            hovermode: "closest"
        })
    })
})