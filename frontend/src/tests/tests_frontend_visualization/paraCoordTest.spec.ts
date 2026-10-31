import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { ParaCoord } from '../../widgets/charts/para-coord'
import type { PlotlyInstance } from '../../widgets/charts/model/chart.types'
import { regionOf, specsByName as fixtureSpecsByName } from './searchSpaceFixture'

const { renderParaCoordMock } = vi.hoisted(() => ({
    renderParaCoordMock: vi.fn()
}))

const allRes = ref<any[]>([])

const specsByName = ref(fixtureSpecsByName)

const plotlyInstance = ref<PlotlyInstance | null>({ react: vi.fn(), purge: vi.fn() })

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
                region: regionOf('frequency', 'threads'),
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

    it('renders once Plotly has finished loading', async () => {
        plotlyInstance.value = null

        mountComponent()

        await flushPromises()

        expect(renderParaCoordMock).not.toHaveBeenCalled()

        plotlyInstance.value = { react: vi.fn(), purge: vi.fn() }

        await flushPromises()

        expect(renderParaCoordMock).toHaveBeenCalled()
    })

    it('draws with the parameters of the search space', async () => {
        mountComponent()
        await flushPromises()

        allRes.value = [{ configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }]
        await flushPromises()

        expect(renderParaCoordMock.mock.lastCall?.[5]).toEqual(specsByName.value)
    })

    it('draws the trials of its region, also those in which a selected parameter is inactive', async () => {
        const wrapper = mountComponent()

        await wrapper.setProps({
            paraCoordParams: ['frequency', 'threads']
        })
        await flushPromises()

        const active = { configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }
        const inactive = { configurations: { frequency: 50 }, results: { runtime: 90 } }
        allRes.value = [active, inactive]

        await flushPromises()

        expect(renderParaCoordMock.mock.lastCall?.[2]).toEqual([active, inactive])
    })

    it('leaves out the trials of other regions', async () => {
        mountComponent()

        await flushPromises()

        const own = { configurations: { frequency: 60, threads: 8 }, results: { runtime: 100 } }
        const other = { configurations: { elsewhere: 1 }, results: { runtime: 90 } }
        allRes.value = [own, other]

        await flushPromises()

        expect(renderParaCoordMock.mock.lastCall?.[2]).toEqual([own])
    })
})
