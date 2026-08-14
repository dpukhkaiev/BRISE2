import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Rank } from '../../widgets/charts/rank'

const { renderRankMock } = vi.hoisted(() => ({
    renderRankMock: vi.fn()
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

vi.mock('../../widgets/charts/rank/render', () => ({
    renderRank: renderRankMock
}))

describe('Rank Plot', () => {

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
        return mount(Rank, {
            props: {
                rankParam1: 'threads',
                rankParam2: 'frequency',
                rankObjective: 'runtime'
            },
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('rerenders when allRes changes', async () => {
        mountComponent()

        await flushPromises()

        const callsBeforeChange = renderRankMock.mock.calls.length

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

        expect(renderRankMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when rankParam1 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderRankMock.mock.calls.length

        await wrapper.setProps({
            rankParam1: 'frequency'
        })

        await flushPromises()

        expect(renderRankMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when rankParam2 changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderRankMock.mock.calls.length

        await wrapper.setProps({
            rankParam2: 'threads'
        })

        await flushPromises()

        expect(renderRankMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })

    it('rerenders when rankObjective changes', async () => {
        const wrapper = mountComponent()

        await flushPromises()

        const callsBeforeChange = renderRankMock.mock.calls.length

        await wrapper.setProps({
            rankObjective: 'energy'
        })

        await flushPromises()

        expect(renderRankMock.mock.calls.length)
            .toBeGreaterThan(callsBeforeChange)
    })
})