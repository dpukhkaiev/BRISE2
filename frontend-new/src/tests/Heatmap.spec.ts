import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import Heatmap from '@/widgets/charts/heatmap/ui/Heatmap.vue'

// mock plotly so it is recognized for ES-modules
vi.mock('plotly.js-dist-min', () => {
    const mockReact = vi.fn();
    return {
        __esModule: true,
        default: { react: mockReact },
        react: mockReact
    };
});

// import mock directly
import Plotly from 'plotly.js-dist-min';

vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
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
        const wrapper = mountComponent()
        await flushPromises()

        if (eventCallbacks['NEW']) {
            eventCallbacks['NEW']({ body: JSON.stringify([{ configurations: { frequency: 'f1', threads: 't1' }, results: [0.85] }]) })
        }

        await flushPromises()

        expect(Plotly.react).toHaveBeenCalled()
    })


    it('should process the FINAL event and render the solution star trace', async () => {
        const wrapper = mountComponent()
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

        expect(Plotly.react).toHaveBeenCalled()

        const lastCallData = vi.mocked(Plotly.react).mock.calls[0][1]
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

        expect(Plotly.react).toHaveBeenCalled()
    })
})