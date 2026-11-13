import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { renderRank } from '../../widgets/charts/rank/render'
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

describe('renderRank', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('purges the plot when allRes is empty', () => {
        const element = document.createElement('div')

        const emptyAllRes = ref<PointExp[]>([])
        renderRank(plotly, element, emptyAllRes.value, 'frequency', 'threads', 'runtime', {})

        expect(plotly.purge).toHaveBeenCalledWith(element)
        expect(plotly.react).not.toHaveBeenCalled()
    })

    it('renders the correct labels and values', () => {
        const element = document.createElement('div')

        const testData: PointExp[] = [
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: {
                    runtime: 30
                },
                time: '1m 0s',
                'measured points': 1
            },
            {
                configurations: {
                    frequency: 60,
                    threads: 8
                },
                results: {
                    runtime: 10
                },
                time: '2m 0s',
                'measured points': 2
            },
            {
                configurations: {
                    frequency: 70,
                    threads: 16
                },
                results: {
                    runtime: 20
                },
                time: '3m 0s',
                'measured points': 3
            }
        ]

        renderRank(plotly, element, testData, 'frequency', 'threads', 'runtime', {})

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
                y: [4, 8, 16],

                marker: {
                    size: 10,
                    color: [30, 10, 20],
                    colorscale: "Portland",
                    colorbar: {
                        title: {
                            text: 'runtime'
                        }
                    }
                },

                text: [
                    'Trial 1',
                    'Trial 2',
                    'Trial 3'
                ],

                hovertemplate:
                    `frequency: %{customdata[0]}<br>` +
                    `threads: %{customdata[1]}<br>` +
                    `runtime: %{marker.color}<extra></extra>`,

                customdata: [
                    [50, 4],
                    [60, 8],
                    [70, 16]
                ]
            }
        ])
    })

    it('sets the correct layout', () => {
        const element = document.createElement('div')

        renderRank(plotly, element, allRes.value, 'frequency', 'threads', 'runtime', {})

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual(
            {
                autosize: true,
                title: {
                    text: "Rank Plot"
                },

                xaxis: {
                    title: {
                        text: 'frequency'
                    }
                },

                yaxis: {
                    title: {
                        text: 'threads'
                    }
                },

                hovermode: "closest"
            } 
        )
    })

    describe('a trial in which a parameter is inactive', () => {
        const trial = (configurations: Record<string, unknown>, runtime: number): PointExp =>
            ({ configurations, results: { runtime }, time: '1m 0s', 'measured points': 1 })

        const level = 'Context.SearchSpace.Algorithm.A.level'
        const size = 'Context.SearchSpace.Algorithm.A.size'
        const ordinal: ParameterSpec = {
            Name: level, Type: 'OrdinalHyperparameter', Level: 1, Categories: [`${level}.low`, `${level}.high`], Inactive: 'inactive'
        }
        const nominal: ParameterSpec = { ...ordinal, Type: 'NominalHyperparameter' }
        const numeric: ParameterSpec = { Name: size, Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 9, Inactive: -7 }

        const render = (trials: PointExp[], first: ParameterSpec, second: ParameterSpec) => {
            renderRank(plotly, document.createElement('div'), trials, first.Name, second.Name, 'runtime', {
                [first.Name]: first,
                [second.Name]: second
            })
            const [, data, layout] = plotly.react.mock.calls[0]
            return { trace: data[0], xaxis: layout.xaxis, yaxis: layout.yaxis }
        }

        it('is drawn next to the first category of an ordinal parameter', () => {
            const trials = [trial({ [level]: `${level}.high`, [size]: 3 }, 10), trial({ [size]: 5 }, 20)]

            const { trace, xaxis } = render(trials, ordinal, numeric)

            expect(trace.x).toEqual([1, -1])
            expect(xaxis.tickvals).toEqual([-1, 0, 1])
            expect(xaxis.ticktext).toEqual(['inactive', 'low', 'high'])
            expect(trace.customdata).toEqual([[`${level}.high`, 3], ['inactive', 5]])
        })

        it('is drawn next to the first observed category of a nominal parameter', () => {
            const trials = [trial({ [level]: `${level}.high`, [size]: 3 }, 10), trial({ [size]: 5 }, 20)]

            const { trace, xaxis } = render(trials, nominal, numeric)

            expect(trace.x).toEqual([0, -1])
            expect(xaxis.tickvals).toEqual([-1, 0])
            expect(xaxis.ticktext).toEqual(['inactive', `${level}.high`])
        })

        it('is drawn below the lower bound of a numeric parameter, on a labelled tick', () => {
            const trials = [trial({ [level]: `${level}.low`, [size]: 3 }, 10), trial({ [level]: `${level}.high` }, 20)]

            const { trace, yaxis } = render(trials, ordinal, numeric)

            expect(trace.y[0]).toBe(3)
            expect(trace.y[1]).toBeLessThan(1)
            expect(yaxis.tickvals[0]).toBe(trace.y[1])
            expect(yaxis.ticktext[0]).toBe('inactive')
            expect(trace.customdata[1]).toEqual([`${level}.high`, 'inactive'])
        })

        it('adds no inactive mark when every parameter is active in every trial', () => {
            const trials = [trial({ [level]: `${level}.low`, [size]: 3 }, 10), trial({ [level]: `${level}.high`, [size]: 5 }, 20)]

            const { xaxis, yaxis } = render(trials, ordinal, numeric)

            expect(xaxis.ticktext).toEqual(['low', 'high'])
            expect(yaxis.tickvals).toBeUndefined()
        })
    })
})
