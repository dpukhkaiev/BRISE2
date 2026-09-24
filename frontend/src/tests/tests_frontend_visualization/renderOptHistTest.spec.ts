import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { renderOptHist } from '../../widgets/charts/opt-hist/render'
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

describe('renderOptHist', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when allRes is empty', () => {
        const element = document.createElement('div')

        const emptyAllRes = ref<PointExp[]>([])
        renderOptHist(element, emptyAllRes.value, experiment_description.value, 'runtime')

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

        renderOptHist(element, testData, experiment_description.value, 'runtime')

        expect(Plotly.react).toHaveBeenCalledTimes(1)

        const call = vi.mocked(Plotly.react).mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                x: [1, 2, 3],
                y: [30, 10, 20],
                type: 'scattergl' as const,
                mode: 'lines+markers' as const,
                line: {
                    color: 'rgba(67,67,67,1)',
                    width: 1,
                    shape: 'spline' as const,
                    dash: 'dot' as const
                },
                text: [
                    'frequency: 50',
                    'frequency: 60',
                    'frequency: 70'
                ],
                marker: {
                    color: 'rgba(255,64,129,1)',
                    size: 8,
                    symbol: 'x' as const
                },
                name: 'results'
            },
            {
                x: [1, 2, 3],
                y: [30, 10, 10],
                type: 'scattergl' as const,
                mode: 'lines+markers' as const,
                line: {
                    color: 'rgba(67,67,67,1)',
                    width: 2,
                    shape: 'spline' as const
                },
                name: 'best point',
                marker: {
                    size: 6,
                    symbol: 'x' as const,
                    color: 'rgba(67,67,67,1)'
                }
            },
            {
                x: [1, 3],
                y: [30, 10],
                type: 'scattergl' as const,
                mode: 'markers' as const,
                hoverinfo: 'none' as const,
                showlegend: false,
                marker: {
                    color: 'rgba(255,64,129,1)',
                    size: 10
                }
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderOptHist(element, allRes.value, experiment_description.value, 'runtime')

        const call = vi.mocked(Plotly.react).mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
            title: {
                text: 'The best results'
            },
            showlegend: true,
            autosize: true,
            xaxis: {
                title: { text: 'Sequence number' },
                showline: true,
                showgrid: false,
                zeroline: false,
                showticklabels: true,
                linecolor: 'rgb(204,204,204)',
                linewidth: 2,
                autotick: false,
                ticks: 'outside' as const,
                tickcolor: 'rgb(204,204,204)',
                tickwidth: 2,
                ticklen: 5,
                tickfont: {
                    family: 'Roboto',
                    size: 12,
                    color: 'rgb(82, 82, 82)'
                }
            },
            yaxis: {
                title: { text: 'runtime' },
                showgrid: false,
                zeroline: false,
                showline: true,
                linecolor: 'rgb(204,204,204)',
                showticklabels: true,
                ticks: 'outside' as const,
                tickcolor: 'rgb(204,204,204)',
                ticklen: 5,
                tickfont: {
                    family: 'Roboto',
                    size: 12,
                    color: 'rgb(82, 82, 82)'
                }
            }
        })
    })
})