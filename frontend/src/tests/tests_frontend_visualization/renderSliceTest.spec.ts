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

    describe('a trial in which the parameter is inactive', () => {
        const trial = (configurations: Record<string, unknown>, runtime: number): PointExp =>
            ({ configurations, results: { runtime }, time: '1m 0s', 'measured points': 1 })

        const level = 'Context.SearchSpace.Algorithm.A.level'
        const ordinal: ParameterSpec = {
            Name: level, Type: 'OrdinalHyperparameter', Level: 1, Categories: [`${level}.low`, `${level}.high`], Inactive: 'inactive'
        }
        const nominal: ParameterSpec = { ...ordinal, Type: 'NominalHyperparameter' }
        const numeric: ParameterSpec = { Name: level, Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 10, Inactive: -10 }

        const render = (spec: ParameterSpec, trials: PointExp[]) => {
            renderSlice(plotly, document.createElement('div'), trials, level, 'runtime', { [level]: spec })
            const [, data, layout] = plotly.react.mock.calls[0]
            return { trace: data[0], xaxis: layout.xaxis }
        }

        it('is drawn at the position next to the first category of an ordinal parameter', () => {
            const { trace, xaxis } = render(ordinal, [trial({ [level]: `${level}.high` }, 10), trial({}, 20)])

            expect(trace.x).toEqual([1, -1])
            expect(xaxis.tickvals).toEqual([-1, 0, 1])
            expect(xaxis.ticktext).toEqual(['inactive', 'low', 'high'])
            expect(trace.customdata).toEqual([`${level}.high`, 'inactive'])
        })

        it('is drawn at the inactive category of a nominal parameter', () => {
            const { trace } = render(nominal, [trial({ [level]: `${level}.high` }, 10), trial({}, 20)])

            expect(trace.x).toEqual([`${level}.high`, 'inactive'])
        })

        it.each([
            ['after', [trial({ [level]: `${level}.high` }, 10), trial({}, 20)]],
            ['before', [trial({}, 20), trial({ [level]: `${level}.high` }, 10)]]
        ])('is the first category of a nominal axis when its trial comes %s the others', (_, trials) => {
            const { xaxis } = render(nominal, trials)

            expect(xaxis.categoryorder).toBe('array')
            expect(xaxis.categoryarray).toEqual(['inactive', `${level}.low`, `${level}.high`])
        })

        it('leaves the order of a nominal axis to Plotly when the parameter is active in every trial', () => {
            const { xaxis } = render(nominal, [trial({ [level]: `${level}.high` }, 10), trial({ [level]: `${level}.low` }, 20)])

            expect(xaxis.categoryorder).toBeUndefined()
        })

        it('is drawn below the lower bound of a numeric parameter, on a labelled tick', () => {
            const { trace, xaxis } = render(numeric, [trial({ [level]: 4 }, 10), trial({}, 20)])

            expect(trace.x[0]).toBe(4)
            expect(trace.x[1]).toBeLessThan(0)
            expect(xaxis.tickvals[0]).toBe(trace.x[1])
            expect(xaxis.ticktext[0]).toBe('inactive')
        })

        it('adds no inactive mark when the parameter is active in every trial', () => {
            const trials = [trial({ [level]: 4 }, 10), trial({ [level]: 5 }, 20)]

            expect(render(numeric, trials).xaxis.ticktext).toBeUndefined()
        })
    })
})
