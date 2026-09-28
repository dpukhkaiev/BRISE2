import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { OptHist } from '../../widgets/charts/opt-hist'
import type { PointExp } from '../../entities/main/model/plot.store'

const { renderOptHistMock } = vi.hoisted(() => ({
    renderOptHistMock: vi.fn()
}))

const allRes = ref<any[]>([])
const solution = ref<PointExp | null>(null)

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

const plotlyInstance = ref({ react: vi.fn(), purge: vi.fn() })

vi.mock('../../entities/main/model/plot.store', () => ({
    usePlotStore: vi.fn(() => ({
        allRes,
        solution
    }))
}))

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description,
        plotlyInstance
    }))
}))

vi.mock('../../widgets/charts/opt-hist/render', () => ({
    renderOptHist: renderOptHistMock
}))

describe('Optimization History', () => {

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.clearAllMocks()

        allRes.value = []
        solution.value = null

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
        return mount(OptHist, {
            props: {
                optHistObjective: 'runtime'
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('rerenders when allRes changes', async () => {
        mountComponent()

        await flushPromises()

        const callsBeforeChange = renderOptHistMock.mock.calls.length

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

        expect(renderOptHistMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when optHistObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderOptHistMock.mock.calls.length

        await wrapper.setProps({
            optHistObjective: 'energy'
        })

        await flushPromises()

        expect(renderOptHistMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('purges the chart when it is unmounted', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const element = wrapper.find('div').element

        wrapper.unmount()

        expect(plotlyInstance.value.purge).toHaveBeenCalledWith(element)
    })
})