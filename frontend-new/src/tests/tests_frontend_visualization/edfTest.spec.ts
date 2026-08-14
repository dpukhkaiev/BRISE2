import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Edf } from '../../widgets/charts/edf'

const { renderEdfMock } = vi.hoisted(() => ({
    renderEdfMock: vi.fn()
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

vi.mock('../../widgets/charts/edf/render', () => ({
    renderEdf: renderEdfMock
}))

describe('EDF Plot', () => {

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
            }
        }
    })

    const mountComponent = () => {
        return mount(Edf, {
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('rerenders when allRes changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderEdfMock.mock.calls.length

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

        expect(renderEdfMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)

        expect(renderEdfMock).toHaveBeenLastCalledWith(
            wrapper.find('div').element,
            allRes.value
        )
    })
})