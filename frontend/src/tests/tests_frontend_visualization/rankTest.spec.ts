import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Rank } from '../../widgets/charts/rank'
import { specsByName as fixtureSpecsByName } from './searchSpaceFixture'

const { renderRankMock } = vi.hoisted(() => ({
    renderRankMock: vi.fn()
}))

const allRes = ref<any[]>([])

const specsByName = ref(fixtureSpecsByName)

const plotlyInstance = ref({ react: vi.fn(), purge: vi.fn() })

vi.mock('../../entities/main/model/plot.store', () => ({
    usePlotStore: vi.fn(() => ({
        allRes
    }))
}))

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        specsByName,
        plotlyInstance
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

    it('draws with the parameters of the search space', async () => {
        mountComponent()
        await flushPromises()

        allRes.value = [{ configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }]
        await flushPromises()

        expect(renderRankMock.mock.lastCall?.[6]).toEqual(specsByName.value)
    })

    it('leaves out trials in which a selected parameter is inactive', async () => {
        mountComponent()

        await flushPromises()

        const active = { configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }
        const inactive = { configurations: { frequency: 50 }, results: { runtime: 90 } }
        allRes.value = [active, inactive]

        await flushPromises()

        expect(renderRankMock.mock.lastCall?.[2]).toEqual([active])
    })
})
