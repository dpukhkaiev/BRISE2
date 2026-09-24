import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { renderContour } from '../../widgets/charts/contour/render'
import type { ExperimentDescription } from '../../entities/experiment/model/experiment.model'

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
                },
                energy: {
                    Name: 'energy',
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
        SearchSpace: {
            "frequency": {
                "twelve_hundred_hertz": {
                    "Type": "Category"
                },
                "thirteen_hundred_hertz": {
                    "Type": "Category"
                },
                "fourteen_hundred_hertz": {
                    "Type": "Category"
                },
                "fifteen_hundred_hertz": {
                    "Type": "Category"
                },
                "sixteen_hundred_hertz": {
                    "Type": "Category"
                },
                "seventeen_hundred_hertz": {
                    "Type": "Category"
                },
                "eighteen_hundred_hertz": {
                    "Type": "Category"
                },
                "nineteen_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_one_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_two_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_three_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_four_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_five_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_six_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_seven_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_eight_hundred_hertz": {
                    "Type": "Category"
                },
                "twenty_nine_hundred_hertz": {
                    "Type": "Category"
                },
                "turbo": {
                    "Type": "Category"
                },
                "Categories": [
                    "Context.SearchSpace.frequency.twelve_hundred_hertz",
                    "Context.SearchSpace.frequency.thirteen_hundred_hertz",
                    "Context.SearchSpace.frequency.fourteen_hundred_hertz",
                    "Context.SearchSpace.frequency.sixteen_hundred_hertz",
                    "Context.SearchSpace.frequency.seventeen_hundred_hertz",
                    "Context.SearchSpace.frequency.eighteen_hundred_hertz",
                    "Context.SearchSpace.frequency.nineteen_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_two_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_three_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_four_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_five_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_seven_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_eight_hundred_hertz",
                    "Context.SearchSpace.frequency.twenty_nine_hundred_hertz",
                    "Context.SearchSpace.frequency.turbo"
                ],
                "Default": "Context.SearchSpace.frequency.twenty_nine_hundred_hertz",
                "Type": "OrdinalHyperparameter",
                "Level": 0
            },
            "threads": {
                "one": {
                    "Type": "Category"
                },
                "two": {
                    "Type": "Category"
                },
                "four": {
                    "Type": "Category"
                },
                "eight": {
                    "Type": "Category"
                },
                "sixteen": {
                    "Type": "Category"
                },
                "thirty_two": {
                    "Type": "Category"
                },
                "Categories": [
                    "Context.SearchSpace.threads.one",
                    "Context.SearchSpace.threads.two",
                    "Context.SearchSpace.threads.four",
                    "Context.SearchSpace.threads.eight",
                    "Context.SearchSpace.threads.sixteen",
                    "Context.SearchSpace.threads.thirty_two"
                ],
                "Default": "Context.SearchSpace.threads.thirty_two",
                "Type": "OrdinalHyperparameter",
                "Level": 0
            },
            "Structure": {
                "Flat": {}
            }
        }
    },
    PlotSelection: {
        Plot: {
            ContourPlot: {}
        }
    }
})

vi.mock('plotly.js-dist-min', () => ({
    default: {
        react: vi.fn(),
        purge: vi.fn()
    }
}))

describe('renderContour', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when backend result is empty', () => {
        const element = document.createElement('div')

        renderContour(element, {}, {} as ExperimentDescription)

        expect(Plotly.purge).toHaveBeenCalledWith(element)
        expect(Plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        renderContour(element, 
            {
                contour: {
                    x: [50, 60],
                    y: [4, 8],
                    z: [
                        [1, 2],
                        [3, 4]
                    ],
                    x_name: 'frequency',
                    y_name: 'threads',
                    objective_name: 'runtime'
                }
            },
            experiment_description.value
        )

        expect(Plotly.react).toHaveBeenCalledTimes(1)

        const call = vi.mocked(Plotly.react).mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data[0]).toEqual(
            expect.objectContaining({
                type: 'contour',
                x: [50, 60],
                y: [4, 8],
                colorscale: 'Portland',
                contours: {
                    coloring: 'heatmap',
                    showlabels: false
                },
                colorbar: {
                    title: {
                        text: 'runtime'
                    }
                }
            })
        )

        expect(data[0].z).toEqual(expect.any(Array))
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderContour(element, 
            {
                contour: {
                    x: [50, 60],
                    y: [4, 8],
                    z: [
                        [1, 2],
                        [3, 4]
                    ],
                    x_name: 'frequency',
                    y_name: 'threads',
                    objective_name: 'runtime'
                }
            },
            experiment_description.value
        )

        const call = vi.mocked(Plotly.react).mock.calls[0]
        const layout = call[2] as any

        const frequencyCategories =
            experiment_description.value.Context?.SearchSpace?.frequency.Categories

        const threadsCategories = 
            experiment_description.value.Context?.SearchSpace?.threads.Categories

        
        expect(layout.xaxis).toEqual({
            tickvals: frequencyCategories?.map((_, index) => index),
            ticktext: frequencyCategories?.map(category => {
                const name = String(category).split('.').pop() ?? String(category)
                return name.replace(/_/g, ' ')
            }),
            title: {
                text: 'frequency'
            }
        })

        expect(layout.yaxis).toEqual({
            tickvals: threadsCategories?.map((_, index) => index),
            ticktext: threadsCategories?.map(category => {
                const name = String(category).split('.').pop() ?? String(category)
                return name.replace(/_/g, ' ')
            }),
            title: {
                text: 'threads'
            }
        })
    })
})