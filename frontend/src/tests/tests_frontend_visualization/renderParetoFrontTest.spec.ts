import { describe, it, expect, vi, beforeEach } from 'vitest'
import Plotly from 'plotly.js-dist-min'
import { renderParetoFront } from '../../widgets/charts/pareto-front/render'

vi.mock('plotly.js-dist-min', () => ({
    default: {
        react: vi.fn(),
        purge: vi.fn()
    }
}))

describe('renderHypImp', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when objectives are empty', () => {
        const element = document.createElement('div')

        renderParetoFront(element, {
            "objective_names": [],
            "all_points": [
                {
                    'energy': 100,
                    'runtime': 150
                },
                {
                    'energy': 120,
                    'runtime': 160
                }
            ],
            "pareto_points": [
                {
                    'energy': 100,
                    'runtime': 150
                }
            ]
        },
        false
    )

        expect(Plotly.purge).toHaveBeenCalledWith(element)
        expect(Plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        renderParetoFront(element, {
            "objective_names": ['energy', 'runtime'],
            "all_points": [
                {
                    'x': 100,
                    'y': 150,
                    'number': 1
                },
                {
                    'x': 120,
                    'y': 160,
                    'number': 2
                }
            ],
            "pareto_points": [
                {
                    'x': 100,
                    'y': 150,
                    'number': 1
                }
            ]},
            true
        )

        expect(Plotly.react).toHaveBeenCalledTimes(1)

        const call = vi.mocked(Plotly.react).mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                x: [100],
                y: [150],
                mode: "markers" as const,
                type: "scatter" as const,
                name: "Pareto front",
                marker: {
                    size: 10,
                    color: "red",
                    symbol: "diamond"
                },
                text: [
                    'Trial 1'
                ],
                hovertemplate:
                    "%{text}<br>" +
                    'energy' +
                    ": %{x}<br>" +
                    'runtime' +
                    ": %{y}<extra></extra>"
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderParetoFront(element, {
            "objective_names": ['energy', 'runtime'],
            "all_points": [
                {
                    'x': 100,
                    'y': 150,
                    'number': 1
                },
                {
                    'x': 120,
                    'y': 160,
                    'number': 2
                }
            ],
            "pareto_points": [
                {
                    'x': 100,
                    'y': 150,
                    'number': 1
                }
            ]},
            true
        )

        const call = vi.mocked(Plotly.react).mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
            title: {
                text: "Pareto Front" 
            },
            xaxis: {
                title: {
                    text: 'energy'
                }
            },
            yaxis: {
                title: {
                    text: 'runtime'
                }
            },
            hovermode: "closest" as const
        })
    })
})