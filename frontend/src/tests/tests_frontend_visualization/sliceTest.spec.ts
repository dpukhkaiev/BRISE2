import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Slice } from '../../widgets/charts/slice'
import { regionOf, specsByName as fixtureSpecsByName } from './searchSpaceFixture'

const { renderSliceMock } = vi.hoisted(() => ({
    renderSliceMock: vi.fn()
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

vi.mock('../../widgets/charts/slice/render', () => ({
    renderSlice: renderSliceMock
}))

describe('Slice Plot', () => {

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.clearAllMocks()

        allRes.value = []

    })

   const mountComponent = () => {
        return mount(Slice, {
            props: {
                region: regionOf('frequency', 'threads'),
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

    it('draws with the parameters of the search space', async () => {
        mountComponent()
        await flushPromises()

        allRes.value = [{ configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }]
        await flushPromises()

        expect(renderSliceMock.mock.lastCall?.[5]).toEqual(specsByName.value)
    })

    it('draws the trials of its region, also those in which the selected parameter is inactive', async () => {
        mountComponent()

        await flushPromises()

        const active = { configurations: { frequency: 60 }, results: { runtime: 100 } }
        const inactive = { configurations: { threads: 8 }, results: { runtime: 90 } }
        allRes.value = [active, inactive]

        await flushPromises()

        expect(renderSliceMock.mock.lastCall?.[2]).toEqual([active, inactive])
    })

    it('leaves out the trials of other regions', async () => {
        mountComponent()

        await flushPromises()

        const own = { configurations: { frequency: 60 }, results: { runtime: 100 } }
        const other = { configurations: { elsewhere: 1 }, results: { runtime: 90 } }
        allRes.value = [own, other]

        await flushPromises()

        expect(renderSliceMock.mock.lastCall?.[2]).toEqual([own])
    })
})
