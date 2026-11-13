import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderContour } from '../../widgets/charts/contour/render'
import type { ParameterSpec } from '../../entities/experiment/model/experiment.model'

const FREQUENCY = 'Context.SearchSpace.frequency'
const THREADS = 'Context.SearchSpace.threads'

const frequencyCategories = ['twelve_hundred_hertz', 'thirteen_hundred_hertz', 'twenty_nine_hundred_hertz', 'turbo']
    .map(name => `${FREQUENCY}.${name}`)
const threadsCategories = ['one', 'two', 'four', 'thirty_two'].map(name => `${THREADS}.${name}`)

const specsByName: Record<string, ParameterSpec> = {
    [FREQUENCY]: { Name: FREQUENCY, Type: 'OrdinalHyperparameter', Level: 0, Categories: frequencyCategories, Inactive: 'inactive' },
    [THREADS]: { Name: THREADS, Type: 'OrdinalHyperparameter', Level: 0, Categories: threadsCategories, Inactive: 'inactive' }
}

const plotly = { react: vi.fn(), purge: vi.fn() }

describe('renderContour', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when backend result is empty', () => {
        const element = document.createElement('div')

        renderContour(plotly, element, {}, specsByName)

        expect(plotly.purge).toHaveBeenCalledWith(element)
        expect(plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        renderContour(plotly, element,
            {
                contour: {
                    x: [50, 60],
                    y: [4, 8],
                    z: [
                        [1, 2],
                        [3, 4]
                    ],
                    x_name: FREQUENCY,
                    y_name: THREADS,
                    objective_name: 'runtime'
                }
            },
            specsByName
        )

        expect(plotly.react).toHaveBeenCalledTimes(1)

        const call = plotly.react.mock.calls[0]

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

        renderContour(plotly, element,
            {
                contour: {
                    x: [50, 60],
                    y: [4, 8],
                    z: [
                        [1, 2],
                        [3, 4]
                    ],
                    x_name: FREQUENCY,
                    y_name: THREADS,
                    objective_name: 'runtime'
                }
            },
            specsByName
        )

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout.xaxis).toEqual({
            tickvals: frequencyCategories.map((_, index) => index),
            ticktext: frequencyCategories.map(category => {
                const name = String(category).split('.').pop() ?? String(category)
                return name.replace(/_/g, ' ')
            }),
            title: {
                text: 'frequency'
            }
        })

        expect(layout.yaxis).toEqual({
            tickvals: threadsCategories.map((_, index) => index),
            ticktext: threadsCategories.map(category => {
                const name = String(category).split('.').pop() ?? String(category)
                return name.replace(/_/g, ' ')
            }),
            title: {
                text: 'threads'
            }
        })
    })
})