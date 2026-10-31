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


    const mountWith = async (regions: SearchSpaceRegion[]) => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(true, regions) as any)
        mountComponent()
        await flushPromises()
        eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: [0.85] }]) })
        await flushPromises()
        return PlotlyMock.react.mock.calls.at(-1)![1][0] as { x: string[], y: string[] }
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

    it('should leave the axes empty when the top-level region has fewer than two parameters', async () => {
        const surface = await mountWith([{ ActivationCategory: 'root', Parameters: [threads] }, defaultRegions[1]])

        expect(surface.y).toEqual([])
        expect(surface.x).toEqual([])
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