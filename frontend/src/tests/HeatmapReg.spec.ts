import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import HeatmapReg from '@/widgets/charts/heatmap-reg/ui/HeatmapReg.vue'
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
    MainEvent: { NEW: 'NEW', FINAL: 'FINAL', DEFAULT: 'DEFAULT', PREDICTIONS: 'PREDICTIONS'}
}))

let eventCallbacks: Record<string, Function> = {}

const mountComponent = () => mount(HeatmapReg, {
    global: { plugins: [createPinia()] }
})

describe('HeatmapReg.vue', () => {
    beforeEach(() => {
        Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, value: 500 })
        Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, value: 800 })
        setActivePinia(createPinia())
        vi.clearAllMocks()
        eventCallbacks = {}
    })

    it('does not render when container has zero height', async () => {
        Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, value: 0 })
        mountComponent()
        await flushPromises()
        expect(PlotlyMock.react).not.toHaveBeenCalled()
    })

    it('renders only the optimum marker when predictions are empty but solution exists', async () => {
        mountComponent()
        await flushPromises()

        eventCallbacks['FINAL']({
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: {}, measured_points: [] }])
        })
        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()
        const data = vi.mocked(PlotlyMock.react).mock.calls[0][1]
        expect(data.find((t: any) => t.name === 'Optimum')).toBeTruthy()
    })

    it('matches optimum point only when axis values exist in x/y arrays', async () => {
        mountComponent()
        await flushPromises()

        eventCallbacks['FINAL']({
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([{ configurations: { frequency: 'nonexistent', threads: 't1' }, results: {} }])
        })
        await flushPromises()

        const data = vi.mocked(PlotlyMock.react).mock.calls[0]?.[1]
        const starTrace = data?.find((t: any) => t.name === 'Optimum')
        expect(starTrace).toBeFalsy() // no match, no star
    })

    it('populates the heatmap surface when PREDICTIONS events arrive', async () => {
        mountComponent()
        await flushPromises()

        eventCallbacks['PREDICTIONS']({
            body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: { energy: 100 } }])
        })
        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()
    })

    it('spans the heatmap by the first two parameters of the top-level region', async () => {
        mountComponent()
        await flushPromises()

        eventCallbacks['PREDICTIONS']({
            body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: { energy: 100 } }])
        })
        await flushPromises()

        // the first parameter is the horizontal axis, the second the vertical one
        const surface = vi.mocked(PlotlyMock.react).mock.calls.at(-1)![1][0]
        expect(surface.x).toEqual(['t1', 't2'])
        expect(surface.y).toEqual(['f1', 'f2'])
    })

    it('does not render when searchspaceReady is false', async () => {
        const { useMainEventStore } = await import('../entities/main')
        vi.mocked(useMainEventStore).mockReturnValueOnce(buildMockStore(false) as any)

        mountComponent()
        await flushPromises()

        expect(PlotlyMock.react).not.toHaveBeenCalled()
    })
})