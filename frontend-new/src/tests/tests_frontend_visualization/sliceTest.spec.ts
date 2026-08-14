import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Slice } from '../../widgets/charts/slice'

const { renderSliceMock } = vi.hoisted(() => ({
    renderSliceMock: vi.fn()
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

vi.mock('../../widgets/charts/slice/render', () => ({
    renderSlice: renderSliceMock
}))

describe('Slice Plot', () => {

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
        return mount(Slice, {
            props: {
                sliceObjective: 'runtime',
                sliceParam: 'frequency'
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('rerenders when allRes changes', async () => {
        mountComponent()

        await flushPromises()

        const callsBeforeChange = renderSliceMock.mock.calls.length

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

        expect(renderSliceMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when sliceParam changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderSliceMock.mock.calls.length

        await wrapper.setProps({
            sliceParam: 'threads'
        })

        await flushPromises()

        expect(renderSliceMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when sliceObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderSliceMock.mock.calls.length

        await wrapper.setProps({
            sliceObjective: 'energy'
        })

        await flushPromises()

        expect(renderSliceMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })
})