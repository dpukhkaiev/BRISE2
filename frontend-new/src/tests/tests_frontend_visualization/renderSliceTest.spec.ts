import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { renderSlice } from '../../widgets/charts/slice/render'
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

const experiment_description = ref({
    Context: {
        TaskConfiguration: {
            MaxTasksPerConfiguration: 1,
            MaxTimeToRunTask: 60,
            RepeaterDecisionFunction: '',
            Objectives: {
                runtime: {
                    Name: 'runtime',
                    DataType: 'float',
                    Minimization: true,
                    MinExpectedValue: 0,
                    MaxExpectedValue: Infinity
                }
            },
            ObjectivesDataTypes: ['float'],
            ObjectivesPriorities: [1],
            TaskName: 'testTask',
            Scenario: {
                ws_file: 'test.ws'
            },
            TimeUnit: 'seconds'
        },
        SearchSpace: {}
    },
    PlotSelection: {
        Plot: {
            OptimizationHistory: {}
        }
    }
})

vi.mock('plotly.js-dist-min', () => ({
    default: {
        react: vi.fn(),
        purge: vi.fn()
    }
}))

describe('renderParaCoord', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when allRes is empty', () => {
        const element = document.createElement('div')

        const emptyAllRes = ref<PointExp[]>([])
        renderSlice(element, emptyAllRes.value, 'frequency', 'runtime', experiment_description.value,)

        expect(Plotly.purge).toHaveBeenCalledWith(element)
        expect(Plotly.react).not.toHaveBeenCalled()
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

        renderSlice(element, testData, 'frequency', 'runtime', experiment_description.value)

        expect(Plotly.react).toHaveBeenCalledTimes(1)

        const call = vi.mocked(Plotly.react).mock.calls[0]

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
                    colorscale: "Blues",
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

        renderSlice(element, allRes.value, 'frequency', 'runtime', experiment_description.value,)

        const call = vi.mocked(Plotly.react).mock.calls[0]
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
})