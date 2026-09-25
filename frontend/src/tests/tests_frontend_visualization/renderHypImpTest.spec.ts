import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHypImp } from '../../widgets/charts/hyp-imp/render'

const plotly = { react: vi.fn(), purge: vi.fn() }

describe('renderHypImp', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when backend result is empty', () => {
        const element = document.createElement('div')

        renderHypImp(plotly, element, {})

        expect(plotly.purge).toHaveBeenCalledWith(element)
        expect(plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        renderHypImp(plotly, element, {
            importances: {
                frequency: 0.8,
                threads: 0.2
            }
        })

        expect(plotly.react).toHaveBeenCalledTimes(1)

        const call = plotly.react.mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                x: ['frequency', 'threads'],
                y: [0.8, 0.2],
                type: 'bar'
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderHypImp(plotly, element, {
            importances: {
                frequency: 0.8,
                threads: 0.2
            }
        })

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
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
        })
    })
})