import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { renderParaCoord } from '../../widgets/charts/para-coord/render'
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
        renderParaCoord(plotly, element, emptyAllRes.value, ['frequency'], 'runtime', {})

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

        renderParaCoord(plotly, element, testData, ['frequency'], 'runtime', {})

        expect(plotly.react).toHaveBeenCalledTimes(1)

        const call = plotly.react.mock.calls[0]

        const passedElement = call[0]
        const data = call[1] as any

        expect(passedElement).toBe(element)

        expect(data).toEqual([
            {
                type: 'parcoords',

                line: {
                    showscale: true,
                    colorscale: 'Portland',
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

        renderParaCoord(plotly, element, allRes.value, ['frequency'], 'runtime', {})

        const call = plotly.react.mock.calls[0]
        const layout = call[2] as any

        expect(layout).toEqual({
            autosize: true,
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

    describe('a trial in which the parameter is inactive', () => {
        const trial = (configurations: Record<string, unknown>, runtime: number): PointExp =>
            ({ configurations, results: { runtime }, time: '1m 0s', 'measured points': 1 })

        const level = 'Context.SearchSpace.Algorithm.A.level'
        const ordinal: ParameterSpec = {
            Name: level, Type: 'OrdinalHyperparameter', Level: 1, Categories: [`${level}.low`, `${level}.high`], Inactive: 'inactive'
        }
        const nominal: ParameterSpec = { ...ordinal, Type: 'NominalHyperparameter' }
        const numeric: ParameterSpec = { Name: level, Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 10, Inactive: -10 }

        const dimension = (spec: ParameterSpec, trials: PointExp[]) => {
            renderParaCoord(plotly, document.createElement('div'), trials, [level], 'runtime', { [level]: spec })
            return plotly.react.mock.calls[0][1][0].dimensions[0]
        }

        it('is drawn next to the first category of an ordinal parameter', () => {
            const result = dimension(ordinal, [trial({ [level]: `${level}.high` }, 10), trial({}, 20)])

            expect(result.values).toEqual([1, -1])
            expect(result.range).toEqual([-1, 1])
            expect(result.tickvals).toEqual([-1, 0, 1])
            expect(result.ticktext).toEqual(['inactive', 'low', 'high'])
        })

        it('is drawn next to the first observed category of a nominal parameter', () => {
            const result = dimension(nominal, [trial({ [level]: `${level}.high` }, 10), trial({}, 20)])

            expect(result.values).toEqual([0, -1])
            expect(result.range).toEqual([-1, 0])
            expect(result.tickvals).toEqual([-1, 0])
            expect(result.ticktext).toEqual(['inactive', 'high'])
        })

        it('is drawn below the lower bound of a numeric parameter, on a labelled tick', () => {
            const result = dimension(numeric, [trial({ [level]: 4 }, 10), trial({}, 20)])

            expect(result.values[0]).toBe(4)
            expect(result.values[1]).toBeLessThan(0)
            expect(result.range).toEqual([result.values[1], 4])
            expect(result.tickvals[0]).toBe(result.values[1])
            expect(result.ticktext[0]).toBe('inactive')
        })

        it('is left undefined for a numeric parameter that has no description', () => {
            renderParaCoord(plotly, document.createElement('div'), [trial({ [level]: 4 }, 10), trial({}, 20)], [level], 'runtime', {})

            expect(plotly.react.mock.calls[0][1][0].dimensions[0].values).toEqual([4, undefined])
        })

        it('adds no inactive mark when the parameter is active in every trial', () => {
            const result = dimension(ordinal, [trial({ [level]: `${level}.high` }, 10), trial({ [level]: `${level}.low` }, 20)])

            expect(result.range).toEqual([0, 1])
            expect(result.tickvals).toEqual([0, 1])
            expect(result.ticktext).toEqual(['low', 'high'])
        })
    })
})
