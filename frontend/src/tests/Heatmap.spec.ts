import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import Heatmap from '@/widgets/charts/heatmap/ui/Heatmap.vue'
import HeatmapReg from '@/widgets/charts/heatmap-reg/ui/HeatmapReg.vue'
import { theme } from '../widgets/charts/model/heatmap-theme'
import type { ParameterSpec, SearchSpaceRegion } from '../entities/experiment/model/experiment.model'

globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}

const PlotlyMock = vi.hoisted(() => ({
    react: vi.fn().mockResolvedValue(undefined),
    purge: vi.fn(),
}))

const categorical = (Name: string, Categories: string[]): ParameterSpec => ({
    Name, Type: 'NominalHyperparameter', Level: 0, Categories, Inactive: 'inactive'
})

// the top-level region holds threads and frequency; the second region is only active for one category of threads
const threads = categorical('threads', ['t1', 't2'])
const frequency = categorical('frequency', ['f1', 'f2'])
const defaultRegions: SearchSpaceRegion[] = [
    { ActivationCategory: 'root', Parameters: [threads, frequency] },
    { ActivationCategory: 'Context.SearchSpace.threads.t1', Parameters: [categorical('mode', ['m1', 'm2'])] }
]

function buildMockStore(searchspaceReady = true, regions: SearchSpaceRegion[] = defaultRegions) {
    return {
        plotlyInstance: PlotlyMock,
        experiment_description: ref({
            Context: { TaskConfiguration: { Objectives: { performance: {} } } },
            ConfigurationSelection: {
                Predictor: {
                    Model: {
                        Surrogate: {
                            Instance: { LinearRegression: {} }
                        }
                    }
                }
            }
        }),
        regions: ref(regions),
        searchspaceReady: ref(searchspaceReady),
        experimentFinished: ref(false),
        onEvent: vi.fn((eventType) => ({
            subscribe: vi.fn((callback) => {
                eventCallbacks[eventType] = callback
                return { unsubscribe: vi.fn() }
            })
        }))
    }
}

vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => buildMockStore()),
    MainEvent: { NEW: 'NEW', FINAL: 'FINAL', DEFAULT: 'DEFAULT' }
}))

let eventCallbacks: Record<string, Function> = {}

const mountComponent = () => mount(Heatmap, {
    global: { plugins: [createPinia()] }
})

describe('Heatmap.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        eventCallbacks = {}
    })

    it('should process the NEW event and update measurement points', async () => {
        mountComponent()
        await flushPromises()

        if (eventCallbacks['NEW']) {
            eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: [0.85] }]) })
        }

        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()
    })


    const mountWith = async (regions: SearchSpaceRegion[], configurations: Record<string, string> = { frequency: 'f1', threads: 't1' }) => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(true, regions) as any)
        mountComponent()
        await flushPromises()
        eventCallbacks['NEW']({ body: JSON.stringify([{ configurations, results: { performance: 0.85 } }]) })
        await flushPromises()
        return PlotlyMock.react.mock.calls.at(-1)![1][0] as { x: string[], y: string[], z: (number | null)[][] }
    }

    it('should span the heatmap by the first two parameters of the top-level region', async () => {
        const surface = await mountWith(defaultRegions)

        // the first parameter is the vertical axis, the second the horizontal one
        expect(surface.y).toEqual(['t1', 't2'])
        expect(surface.x).toEqual(['f1', 'f2'])
    })

    it('should show the bounds of a numeric parameter on its axis', async () => {
        const numeric: ParameterSpec = { Name: 'threads', Type: 'IntegerHyperparameter', Level: 0, Lower: 1, Upper: 8, Inactive: -7 }

        const surface = await mountWith([{ ActivationCategory: 'root', Parameters: [numeric, frequency] }])

        expect(surface.y).toEqual(['1', '8'])
        expect(surface.x).toEqual(['f1', 'f2'])
    })

    it('should say so instead of drawing when the top-level region has fewer than two parameters', async () => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(true, [{ ActivationCategory: 'root', Parameters: [threads] }, defaultRegions[1]]) as any)
        const wrapper = mountComponent()
        await flushPromises()
        eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { threads: 't1' }, results: { performance: 0.85 } }]) })
        await flushPromises()

        expect(wrapper.text()).toContain('Not enough parameters in the top-level region for a heatmap.')
        expect(PlotlyMock.react).not.toHaveBeenCalled()
    })

    it('should not say so while a heatmap can be drawn', async () => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(true, defaultRegions) as any)
        const wrapper = mountComponent()
        await flushPromises()

        expect(wrapper.text()).not.toContain('Not enough parameters')
    })

    it('should not say so before main-node has described the search space', async () => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(false, []) as any)
        const wrapper = mountComponent()
        await flushPromises()

        expect(wrapper.text()).not.toContain('Not enough parameters')
    })

    it('should draw a configuration without the horizontal parameter in an inactive column', async () => {
        const surface = await mountWith(defaultRegions, { threads: 't1' })

        expect(surface.x).toEqual(['f1', 'f2', 'inactive'])
        expect(surface.y).toEqual(['t1', 't2'])
        expect(surface.z).toEqual([[null, null, 0.85], [null, null, null]])
    })

    it('should draw a configuration without the vertical parameter in an inactive row', async () => {
        const surface = await mountWith(defaultRegions, { frequency: 'f2' })

        expect(surface.y).toEqual(['t1', 't2', 'inactive'])
        expect(surface.z).toEqual([[null, null], [null, null], [null, 0.85]])
    })

    it('should draw nothing of the previous experiment when the new one has fewer than two top-level parameters', async () => {
        const { useMainEventStore } = await import('../entities/main')
        const store = buildMockStore(true, defaultRegions)
        vi.mocked(useMainEventStore).mockReturnValueOnce(store as any)
        const wrapper = mountComponent()
        await flushPromises()
        eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: { performance: 0.85 } }]) })
        await flushPromises()
        PlotlyMock.react.mockClear()

        // the next experiment has a single top-level parameter
        store.regions.value = [{ ActivationCategory: 'root', Parameters: [threads] }, defaultRegions[1]]
        await flushPromises()
        eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { LLH: 'a' }, results: { performance: 0.85 } }]) })
        eventCallbacks['FINAL']({
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([{ configurations: { LLH: 'a' }, results: { performance: 0.85 } }])
        })
        await flushPromises()

        // Plotly adds a category to an axis for every value it is given, so nothing may be drawn, not even at 'inactive'
        expect(PlotlyMock.react).not.toHaveBeenCalled()
        expect(PlotlyMock.purge).toHaveBeenCalled()
        expect(wrapper.text()).toContain('Not enough parameters in the top-level region for a heatmap.')
    })

    it('should add no inactive row or column when every configuration has both parameters', async () => {
        const surface = await mountWith(defaultRegions)

        expect(surface.x).toEqual(['f1', 'f2'])
        expect(surface.y).toEqual(['t1', 't2'])
    })

    it('should process the FINAL event and render the solution star trace', async () => {
        mountComponent()
        await flushPromises()

        const mockMessage = {
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([
                {
                    configurations: ['final_f', 'final_t'],
                    results: { performance: 0.99 }
                }
            ])
        }

        if (eventCallbacks['FINAL']) {
            eventCallbacks['FINAL'](mockMessage)
        }
        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()

        const lastCallData = vi.mocked(PlotlyMock.react).mock.calls[0][1]
        const starTrace = lastCallData[2] as any

        expect(starTrace.marker.color).toBe('Gold')
        expect(starTrace.marker.symbol).toBe('star')
    })

    it('should re-render the chart when the color scale theme selection changes', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        const selectColor = wrapper.findAll('select').at(0)
        await selectColor?.setValue('Cividis')
        await selectColor?.trigger('change')
        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()
    })

    it('shares the colorscale selection with HeatmapReg', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        const selectColor = wrapper.findAll('select').at(0)
        await selectColor?.setValue('Jet')
        await selectColor?.trigger('change')
        await flushPromises()

        expect(theme.value.color).toBe('Jet')

        const regWrapper = mount(HeatmapReg, {
            global: { plugins: [createPinia()] }
        })
        await flushPromises()

        expect((regWrapper.find('select').element as HTMLSelectElement).value).toBe('Jet')
    })

    it('should not render when searchspaceReady is false', async () => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(false) as any)

        mountComponent()
        await flushPromises()

        expect(PlotlyMock.react).not.toHaveBeenCalled()
    })
})