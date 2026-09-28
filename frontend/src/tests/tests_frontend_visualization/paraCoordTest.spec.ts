import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { ParaCoord } from '../../widgets/charts/para-coord'
import type { PlotlyInstance } from '../../widgets/charts/model/chart.types'

const { renderParaCoordMock } = vi.hoisted(() => ({
    renderParaCoordMock: vi.fn()
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
    }
})

const plotlyInstance = ref<PlotlyInstance | null>({ react: vi.fn(), purge: vi.fn() })

vi.mock('../../entities/main/model/plot.store', () => ({
    usePlotStore: vi.fn(() => ({
        allRes
    }))
}))

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description,
        plotlyInstance
    }))
}))

vi.mock('../../widgets/charts/para-coord/render', () => ({
    renderParaCoord: renderParaCoordMock
}))

describe('Parallel Coordinates', () => {

    let wrapper: VueWrapper | null = null

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.clearAllMocks()

        allRes.value = []
        plotlyInstance.value = { react: vi.fn(), purge: vi.fn() }

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
            }
        }
    })

    // every mounted component keeps its watchers alive until it's unmounted, and they all share
    // the same module-level refs, so a leftover instance from an earlier test would otherwise
    // react to later tests' state changes
    afterEach(() => {
        wrapper?.unmount()
        wrapper = null
    })

   const mountComponent = () => {
        wrapper = mount(ParaCoord, {
            props: {
                paraCoordObjective: 'runtime',
                paraCoordParams: ['frequency, threads']
            },
            global: {
                plugins: [createPinia()]
            }
        })
        return wrapper
    }

    it('rerenders when allRes changes', async () => {
        mountComponent()

        await flushPromises()

        const callsBeforeChange = renderParaCoordMock.mock.calls.length

        allRes.value.push({
            configurations: {
                frequency: 60,
                threads: 8
            },
            results: {
                runtime: 100
            }
        })

        await flushPromises()

        expect(renderParaCoordMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when paraCoordParams changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderParaCoordMock.mock.calls.length

        await wrapper.setProps({
            paraCoordParams: ['frequency']
        })

        await flushPromises()

        expect(renderParaCoordMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when paraCoordObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderParaCoordMock.mock.calls.length

        await wrapper.setProps({
            paraCoordObjective: 'energy'
        })

        await flushPromises()

        expect(renderParaCoordMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('purges the chart when it is unmounted', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const element = wrapper.find('div').element

        wrapper.unmount()

        expect(plotlyInstance.value?.purge).toHaveBeenCalledWith(element)
    })

    it('does not render without an experiment description', async () => {
        experiment_description.value = null as any

        mountComponent()

        await flushPromises()

        allRes.value.push({
            configurations: {
                frequency: 60,
                threads: 8
            },
            results: {
                runtime: 100
            }
        })

        await flushPromises()

        expect(renderParaCoordMock).not.toHaveBeenCalled()
    })

    it('renders once Plotly has finished loading', async () => {
        plotlyInstance.value = null

        mountComponent()

        await flushPromises()

        expect(renderParaCoordMock).not.toHaveBeenCalled()

        plotlyInstance.value = { react: vi.fn(), purge: vi.fn() }

        await flushPromises()

        expect(renderParaCoordMock).toHaveBeenCalled()
    })
})