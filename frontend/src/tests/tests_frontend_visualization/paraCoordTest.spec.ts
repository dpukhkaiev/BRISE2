import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { ParaCoord } from '../../widgets/charts/para-coord'

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

vi.mock('../../widgets/charts/para-coord/render', () => ({
    renderParaCoord: renderParaCoordMock
}))

describe('Parallel Coordinates', () => {

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
            }
        }
    })

   const mountComponent = () => {
        return mount(ParaCoord, {
            props: {
                paraCoordObjective: 'runtime',
                paraCoordParams: ['frequency, threads']
            },
            global: {
                plugins: [createPinia()]
            }
        })
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
})