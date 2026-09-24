import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { ParetoFront } from '../../widgets/charts/pareto-front'

const result = {
    "objective_names": ['energy', 'runtime'],
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
}

const { calculatePlotMock } = vi.hoisted(() => ({
    calculatePlotMock: vi.fn()
}))

const { renderParetoFrontMock } = vi.hoisted(() => ({
    renderParetoFrontMock: vi.fn()
}))

const allRes = ref<any[]>([])

const experiment_description = ref({
    Context: {
        TaskConfiguration: {
            Objectives: {
                runtime: {
                    Name: 'runtime',
                    Minimization: true
                },
                energy: {
                    Name: 'energy',
                    Minimization: true
                }
            }
        },
        SearchSpace: {}
    },
    PlotSelection: {
        Plot: {
            ParetoFront: {}
        }
    }
})

vi.mock('../../entities/main/model/plot.store', () => ({
    usePlotStore: vi.fn(() => ({
        allRes
    }))
}))

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description
    }))
}))

vi.mock('../../entities/main/api/main.client.store', () => ({
    MainClientApi: {
        calculatePlot: calculatePlotMock
    }
}))

vi.mock('../../widgets/charts/pareto-front/render', () => ({
    renderParetoFront: renderParetoFrontMock
}))



describe('Pareto Front', () => {

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.resetAllMocks()

        allRes.value = []

        experiment_description.value = {
            Context: {
                TaskConfiguration: {
                    Objectives: {
                        runtime: {
                            Name: 'runtime',
                            Minimization: true
                        },
                        energy: {
                            Name: 'energy',
                            Minimization: true
                        }
                    }
                },
                SearchSpace: {}
            },
            PlotSelection: {
                Plot: {
                    ParetoFront: {}
                }
            }
        }
    })

    const mountComponent = () => {
        return mount(ParetoFront, {
            props: {
                paretoObjective1: 'energy',
                paretoObjective2: 'runtime',
                onlyShowParetoFront: false
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('calls backend with the correct objectives when allRes changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        allRes.value = [
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4, 234.5],
                time: '10m 20s',
                'measured points': 1
            }
        ]

        await flushPromises()

        expect(calculatePlotMock).toHaveBeenCalled()

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'pareto_front',
            {
                experiment_description: experiment_description.value,
                trials: allRes.value,
                objective1: 'energy',
                objective2: 'runtime'
            }
        )
    })

    it('passes result from backend to render', async () => {

        calculatePlotMock.mockResolvedValue(result)

        const wrapper = mountComponent()

        await flushPromises()

            allRes.value = [
                {
                    configurations: {
                        frequency: 50,
                        threads: 4
                    },
                    results: [100, 150],
                    time: '10m 20s',
                    'measured points': 1
                },
                {
                    configurations: {
                        frequency: 60,
                        threads: 8
                    },
                    results: [120, 160],
                    time: '10m 30s',
                    'measured points': 1
                }
            ]
        
        await flushPromises()

        expect(renderParetoFrontMock).toHaveBeenCalledWith(
            wrapper.find('div').element,
            result,
            false
        )
    })

    it('rerenders when allRes changes', async () => {
        mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        allRes.value.push({
            configurations: {
                frequency: 60,
                threads: 8
            },
            results: [100]
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when paretoObjective1 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            paretoObjective1: 'runtime'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'pareto_front',
            expect.objectContaining({
                objective1: 'runtime'
            })
        )
    })

   it('rerenders when paretoObjective2 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            paretoObjective2: 'energy'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'pareto_front',
            expect.objectContaining({
                objective2: 'energy'
            })
        )
    })

    it('rerenders when onlyShowParetoFront changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            onlyShowParetoFront: true
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('passes an empty result to render if result is empty', async () => {
        const emptyResult = {
            "objective_names": [],
            "all_points": [], 
            "pareto_points": []
        }

        calculatePlotMock.mockResolvedValue(emptyResult)

        const wrapper = mountComponent()

        allRes.value.push({
            configurations: {
                frequency: 50,
                threads: 4
            },
            results: [100, 150],
            time: '10m 20s',
            'measured points': 1
        })

        await flushPromises()

        expect(calculatePlotMock).toHaveBeenCalled()

        expect(renderParetoFrontMock).toHaveBeenLastCalledWith(
            wrapper.find('div').element,
            emptyResult,
            false
        )
    })
})