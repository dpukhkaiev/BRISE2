import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Contour } from '../../widgets/charts/contour'

const result = {
    contour: {
        x: [50, 60],
        y: [4, 8],
        z: expect.any(Array),
        x_name: 'frequency',
        y_name: 'threads',
        objective_name: 'runtime'
    }
}

const { calculatePlotMock } = vi.hoisted(() => ({
    calculatePlotMock: vi.fn()
}))

const { renderContourMock } = vi.hoisted(() => ({
    renderContourMock: vi.fn()
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
            ContourPlot: {}
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

vi.mock('../../widgets/charts/contour/render', () => ({
    renderContour: renderContourMock
}))



describe('Contour Plot', () => {

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
                    ContourPlot: {}
                }
            }
        }
    })

    const mountComponent = () => {
        return mount(Contour, {
            props: {
                contourParam1: 'frequency',
                contourParam2: 'threads',
                contourObjective: 'runtime'
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('calls backend with the correct parameters and objective when allRes changes', async () => {
        mountComponent()

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
            },
            {
                configurations: {
                    frequency: 60,
                    threads: 8
                },
                results: [125.4],
                time: '10m 20s',
                'measured points': 1
            }
        ]

        await flushPromises()

        expect(calculatePlotMock).toHaveBeenCalled()

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            "contour",
            {
                "experiment_description": experiment_description.value,
                "trials": allRes.value,
                "param1": 'frequency',
                "param2": 'threads',
                "objective": 'runtime'
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
                    results: [123.4],
                    time: '10m 20s',
                    'measured points': 1
                }
            ]
        
        await flushPromises()

        expect(renderContourMock).toHaveBeenCalledWith(
            wrapper.find('div').element,
            result,
            experiment_description.value
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

    it('rerenders when contourParam1 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            contourParam1: 'threads'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            "contour",
            {
                "experiment_description": experiment_description.value,
                "trials": allRes.value,
                "param1": 'threads',
                "param2": 'threads',
                "objective": 'runtime'
            }
        )
    })

    it('rerenders when contourParam2 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            contourParam2: 'frequency'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            "contour",
            {
                "experiment_description": experiment_description.value,
                "trials": allRes.value,
                "param1": 'frequency',
                "param2": 'frequency',
                "objective": 'runtime'
            }
        )
    })

    it('rerenders when contourObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = calculatePlotMock.mock.calls.length

        await wrapper.setProps({
            contourObjective: 'energy'
        })

        await flushPromises()

        expect(calculatePlotMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(calculatePlotMock).toHaveBeenLastCalledWith(
            "contour",
            {
                "experiment_description": experiment_description.value,
                "trials": allRes.value,
                "param1": 'frequency',
                "param2": 'threads',
                "objective": 'energy'
            }
        )
    })

    it('passes an empty result to render if result is empty', async () => {
        const emptyResult = {
            contour: {}
        }

        calculatePlotMock.mockResolvedValue(emptyResult)

        const wrapper = mountComponent()

         allRes.value.push({
            configurations: {
                frequency: 50,
                threads: 4
            },
            results: [100],
            time: '10m 20s',
            'measured points': 1
        })

        await flushPromises()

        expect(renderContourMock).toHaveBeenCalledWith(
            wrapper.find('div').element,
            emptyResult,
            experiment_description.value
        )
    })
})