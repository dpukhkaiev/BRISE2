import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { renderParaCoord } from '../../widgets/charts/para-coord/render'
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
        renderParaCoord(element, emptyAllRes.value, ['frequency'], 'runtime', experiment_description.value,)

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

        renderParaCoord(element, testData, ['frequency'], 'runtime', experiment_description.value)

        expect(Plotly.react).toHaveBeenCalledTimes(1)

        const call = vi.mocked(Plotly.react).mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                type: 'parcoords',

                line: {
                    showscale: true,
                    colorscale: 'Jet',
                    color: [30, 10, 20]
                },

                dimensions: [
                    {
                        label: 'frequency',
                        values: [50, 60, 70],
                        range: [50, 70]
                    },
                    {
                        label: 'runtime',
                        values: [30, 10, 20]
                    }
                ]
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderParaCoord(element, allRes.value, ['frequency'], 'runtime', experiment_description.value,)

        const call = vi.mocked(Plotly.react).mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
            margin: {
                l: 150,
            },

            title: {
                text: 'Parallel Coordinates',
                font: {
                    size: 20
                },
                xref: 'paper' as const,
                x: 0.05,
            }   
        })
    })
})