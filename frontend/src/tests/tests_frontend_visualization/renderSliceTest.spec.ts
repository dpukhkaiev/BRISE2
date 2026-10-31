import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { renderSlice } from '../../widgets/charts/slice/render'
import type { PointExp } from '../../entities/main/model/plot.store'
import type { ParameterSpec } from '../../entities/experiment/model/experiment.model'

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

describe('renderParaCoord', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when allRes is empty', () => {
        const element = document.createElement('div')

        const emptyAllRes = ref<PointExp[]>([])
        renderSlice(plotly, element, emptyAllRes.value, 'frequency', 'runtime', {})

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

        renderSlice(plotly, element, testData, 'frequency', 'runtime', {})

        expect(plotly.react).toHaveBeenCalledTimes(1)

        const call = plotly.react.mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                type: "scatter",
                mode: "markers",

                x: [50, 60, 70],

                y: [30, 10, 20],

                text: [
                    `Trial 1`,
                    'Trial 2',
                    'Trial 3'
                ],

                hovertemplate:
                    `frequency: %{customdata}<br>` +
                    `runtime: %{y}<br>` +
                    "Run: %{text}<extra></extra>",

                customdata: [50, 60, 70],

                marker: {
                    size: 8,
                    color: [1, 2, 3],
                    colorscale: "Portland",
                    showscale: true,
                    colorbar: {
                        title: {
                            text: "Run"
                        }
                    }
                },

                showlegend: false
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderSlice(plotly, element, allRes.value, 'frequency', 'runtime', {})

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual(
            {
                title: {
                    text: "Slice Plot"
                },
                autosize: true,
                hovermode: "closest",

                xaxis: {
                    title: {
                        text: 'frequency'
                    }
                },

                yaxis: {
                    title: {
                        text: 'runtime'
                    }
                }
            } 
        )
    })

    it('orders a nested ordinal parameter by its categories', () => {
        const element = document.createElement('div')
        const level = 'Context.SearchSpace.Algorithm.A.level'
        const specsByName: Record<string, ParameterSpec> = {
            [level]: {
                Name: level,
                Type: 'OrdinalHyperparameter',
                Level: 1,
                Categories: [`${level}.low`, `${level}.high`],
                Inactive: 'inactive'
            }
        }
        const trials: PointExp[] = [
            { configurations: { [level]: `${level}.high` }, results: { runtime: 10 }, time: '1m 0s', 'measured points': 1 },
            { configurations: { [level]: `${level}.low` }, results: { runtime: 20 }, time: '2m 0s', 'measured points': 2 }
        ]

        renderSlice(plotly, element, trials, level, 'runtime', specsByName)

        const [, data, layout] = plotly.react.mock.calls[0]
        expect(data[0].x).toEqual([1, 0])
        expect(layout.xaxis.tickvals).toEqual([0, 1])
        expect(layout.xaxis.ticktext).toEqual(['low', 'high'])
    })
})
