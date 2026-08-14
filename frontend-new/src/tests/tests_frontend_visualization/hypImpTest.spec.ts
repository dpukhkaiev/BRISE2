import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { HypImp } from '../../widgets/charts/hyp-imp'

const result = {
    importances: {
        frequency: 0.8,
        threads: 0.2
    }
}

const { calculatePlotMock } = vi.hoisted(() => ({
    calculatePlotMock: vi.fn()
}))

const { renderHypImpMock } = vi.hoisted(() => ({
    renderHypImpMock: vi.fn()
}))

const allRes = ref<any[]>([])

const experiment_description = ref({
    Context: {
        TaskConfiguration: {
            Objectives: {
                runtime: {
                    Name: 'runtime',
                    Minimization: true
                }
            }
        },
        SearchSpace: {}
    },
    PlotSelection: {
        Plot: {
            HyperparameterImportances: {}
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

vi.mock('../../widgets/charts/hyp-imp/render', () => ({
    renderHypImp: renderHypImpMock
}))



describe('Hyperparameter Importances', () => {

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.clearAllMocks()

        allRes.value = []

        experiment_description.value = {
            Context: {
                TaskConfiguration: {
                    Objectives: {
                        runtime: {
                            Name: 'runtime',
                            Minimization: true
                        }
                    }
                },
                SearchSpace: {}
            },
            PlotSelection: {
                Plot: {
                    HyperparameterImportances: {}
                }
            }
        }
    })

    const mountComponent = () => {
        return mount(HypImp, {
            props: {
                hypImpParams: ['frequency', 'threads'],
                hypImpObjective: 'runtime'
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('calls backend with the correct parameters when allRes changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        allRes.value = [
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4],
                time: '10m 20s',
                'measured points': 1
            }
        ]

        await flushPromises()

        expect(calculatePlotMock).toHaveBeenCalled()

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'hyperparameter_importances',
            {
                experiment_description: experiment_description.value,
                trials: allRes.value,
                parameters: ['frequency', 'threads'],
                objective: 'runtime'
            }
        )
    })

    it('passes result from backend to renderHypImp', async () => {

        calculatePlotMock.mockResolvedValue(result)

        const wrapper = mountComponent()

        await flushPromises()

            allRes.value = [
                {
                    configurations: {
                        frequency: 50,
                        threads: 4
                    },
                    results: [123.4],
                    time: '10m 20s',
                    'measured points': 1
                }
            ]
        
        await flushPromises()

        expect(renderHypImpMock).toHaveBeenCalledWith(
            wrapper.find('div').element,
            result
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

    it('rerenders when hypImpParams changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            hypImpParams: ['frequency']
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'hyperparameter_importances',
            expect.objectContaining({
                parameters: ['frequency']
            })
        )
    })

    it('rerenders when hypImpObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            hypImpObjective: 'energy'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            'hyperparameter_importances',
            expect.objectContaining({
                objective: 'energy'
            })
        )
    })

    it('passes an empty importance result to renderHypImp if allRes is empty', async () => {
        const emptyResult = {
            importances: {}
        }

        calculatePlotMock.mockResolvedValue(emptyResult)

        const wrapper = mountComponent()

        await flushPromises()

        expect(renderHypImpMock).toHaveBeenCalledWith(
            wrapper.find('div').element,
            result
        )
    })
})