import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import HeatmapReg from '@/widgets/charts/heatmap-reg/ui/HeatmapReg.vue'


globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
vi.mock('plotly.js-dist-min', () => {
    const mockPlotly = {
        react: vi.fn().mockResolvedValue(undefined),
        purge: vi.fn(),
    }
    return {
        __esModule: true,
        default: mockPlotly,
        ...mockPlotly
    }
})

import PlotlyMock from 'plotly.js-dist-min'

vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
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
        searchspace: ref({
            boundaries: [{
                Boundaries: {
                    threads: ['t1', 't2'],
                    frequency: ['f1', 'f2']
                }
            }]
        }),
        globalConfig: ref({}),
        onEvent: vi.fn((eventType) => ({
            subscribe: vi.fn((callback) => {
                eventCallbacks[eventType] = callback
                return { unsubscribe: vi.fn() }
            })
        }))
    })),
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
        const wrapper = mountComponent()
        await flushPromises()
        expect(PlotlyMock.react).not.toHaveBeenCalled()
    })

    it('renders only the optimum marker when predictions are empty but solution exists', async () => {
        const wrapper = mountComponent()
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
        
        const wrapper = mountComponent()
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
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['PREDICTIONS']({
            body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: { energy: 100 } }])
        })
        await flushPromises()

        expect(PlotlyMock.react).toHaveBeenCalled()
    })
})