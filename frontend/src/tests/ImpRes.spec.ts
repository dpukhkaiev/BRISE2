import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref, defineComponent, h, Suspense } from 'vue'
import ImpRes from '../widgets/charts/imp-res/ui/ImpRes.vue'

vi.mock('plotly.js-dist-min', () => {
    const mockPlotly = {
        react: vi.fn().mockResolvedValue(undefined),
        purge: vi.fn(),
        extendTraces: vi.fn(),
        restyle: vi.fn(),
    }
    return {
        __esModule: true,
        default: mockPlotly,
        ...mockPlotly
    }
})


vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        plotlyInstance: PlotlyMock,
        experiment_description: ref({
         Context: {
                TaskConfiguration: {
                    Objectives: {
                        'runtime': { Minimization: true }
                    }
                }
            },
            TaskConfiguration: {
                Objectives: ['runtime']
            }
        }),
        globalConfig: ref({}),
        // catching the callbacks
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

const mountComponent = () => {
    const TestAsyncWrapper = defineComponent({
        render() {
            return h(Suspense, null, {
                default: () => h(ImpRes),
                fallback: () => h('div', 'Loading...')
            })
        }
    })

    return mount(TestAsyncWrapper, {
        global: {
            plugins: [createPinia()]
        }
    })
}
import PlotlyMock from 'plotly.js-dist-min'


describe('ImpRes.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        // clear the callbacks before every iteration
        eventCallbacks = {}
    })

   it('should call Plotly.react when a DEFAULT event appears', async () => {
    const wrapper = mountComponent()
    await flushPromises()
  // find imp res component in suspense tree
    const impResComponent = wrapper.findComponent(ImpRes)
    if (eventCallbacks['DEFAULT']) {
        eventCallbacks['DEFAULT']({ 
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([
                { 
                         configurations: { 
                        someParameter: 'valueA', 
                        anotherParameter: 'valueB' 
                    }, 
                        results: [99.9] 
                }
            ]) 
        })
    }

    await flushPromises()
    await wrapper.vm.$nextTick()
    
    expect(impResComponent.find('div').isVisible()).toBe(true)
    // check if plotly started painting the chart
    expect(PlotlyMock.react).toHaveBeenCalled()
})

it('NEW event incoming points update the chart', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        const impResComponent = wrapper.findComponent(ImpRes)

        if (eventCallbacks['DEFAULT']) {
            eventCallbacks['DEFAULT']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([{ configurations: { p: 'Start' }, results: [50.0] }])
            })
        }
        await flushPromises()

        if (eventCallbacks['NEW']) {
            eventCallbacks['NEW']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([{ configurations: { p: 'Mitte' }, results: [30.0] }])
            })
        }

        await flushPromises()
        await wrapper.vm.$nextTick()

        
        const lastCallArgs = vi.mocked(PlotlyMock.react).mock.calls.at(-1)
        const passedData = lastCallArgs?.[1] 
        const allResultsTrace = passedData?.[0] as any
        const bestPointsTrace = passedData?.[1] as any

       
        expect(allResultsTrace?.y).toEqual([50.0, 30.0])
        expect(bestPointsTrace?.y).toEqual([50.0, 30.0])
    })

    it('should render the last point when FINAL event incoming', async () => {
        const wrapper = mountComponent()

        if (eventCallbacks['DEFAULT']) {
            eventCallbacks['DEFAULT']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([{ configurations: { p: 'A' }, results: [10.0] }])
            })
        }
        await flushPromises()

        // trigger FINAL event
        if (eventCallbacks['FINAL']) {
            eventCallbacks['FINAL']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([{ configurations: { p: 'Z' }, results: [5.0] }])
            })
        }

        await flushPromises()
        await wrapper.vm.$nextTick()

        
        const lastCallArgs = vi.mocked(PlotlyMock.react).mock.calls.at(-1)
        const passedData = lastCallArgs?.[1] as any

      
        expect(passedData?.[0]?.y.at(-1)).toBe(5.0)
    })
})