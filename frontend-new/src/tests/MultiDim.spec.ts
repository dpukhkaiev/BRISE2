import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick, reactive, toRefs } from 'vue'
import MultiDimComponent from '../widgets/charts/multi-dim/ui/MultiDim.vue'

const { hoistedPlotly, sharedCallbacks, rawSearchspace, rawExperimentDescription } = vi.hoisted(() => {
    return {
        hoistedPlotly: {
            react: vi.fn().mockResolvedValue(undefined),
            purge: vi.fn(),
        },
        sharedCallbacks: {} as Record<string, Function>,
        rawSearchspace: {
            name: 'my_experiment_id',
            root_parameters_list: ['my_experiment_id'],
            boundaries: [{
                Boundaries: {
                    'param.threads': [1, 2, 4],
                    'param.mode': ['auto', 'manual']
                }
            }]
        },
        rawExperimentDescription: {
            Context: {
                TaskConfiguration: {
                    Objectives: { energy: { Minimization: true } }
                }
            }
        }
    }
})

const mockStoreState = reactive({
    searchspace: rawSearchspace,
    experiment_description: rawExperimentDescription,
    plotlyInstance: hoistedPlotly,
    onEvent: vi.fn((eventType) => ({
        subscribe: vi.fn((callback) => {
            sharedCallbacks[eventType] = callback
            return { unsubscribe: vi.fn() }
        })
    }))
})

vi.mock('pinia', async (importOriginal) => {
    const original = await importOriginal<typeof import('pinia')>()
    return {
        ...original,
        storeToRefs: vi.fn(() => toRefs(mockStoreState))
    }
})

vi.mock('plotly.js-dist-min', () => ({
    __esModule: true,
    default: hoistedPlotly,
    ...hoistedPlotly
}))

vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => mockStoreState),
    MainEvent: { NEW: 'NEW', FINAL: 'FINAL', DEFAULT: 'DEFAULT' }
}))

describe('MultiDim', () => {
    beforeEach(() => {
        vi.useFakeTimers()
        vi.clearAllMocks()
        document.body.innerHTML = ''
        for (const key in sharedCallbacks) {
            delete sharedCallbacks[key]
        }
    })

    const mountWithState = () => {
        const div = document.createElement('div')
        document.body.appendChild(div)
        return mount(MultiDimComponent, {
            global: {},
            attachTo: div
        })
    }

    it('should render the DOM element and pass correctly mapped axes to Plotly on a NEW event', async () => {
        const wrapper = mountWithState()
        await flushPromises()
        await nextTick()

        if (sharedCallbacks['NEW']) {
            sharedCallbacks['NEW']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([
                    {
                        configurations: {
                            'param.threads': 2,
                            'param.mode': 'auto'
                        },
                        results: { energy: 42 }
                    }
                ])
            })
        }

        vi.advanceTimersByTime(550)
        await flushPromises()
        await nextTick()

        expect(hoistedPlotly.react).toHaveBeenCalled()
        
        const lastCallArgs = vi.mocked(hoistedPlotly.react).mock.calls.at(-1)
        const passedTrace = lastCallArgs?.[1] as any[]
        const dimensions = passedTrace[0].dimensions

        expect(dimensions).toHaveLength(3)
        expect(dimensions[0].label).toBe('threads')
        expect(dimensions[0].values).toEqual([2])
        expect(dimensions[1].label).toBe('mode')
        expect(dimensions[1].ticktext).toEqual(['auto', 'manual'])
        expect(dimensions[1].values).toEqual([0])
        expect(dimensions[2].label).toBe('result')
        expect(dimensions[2].values).toEqual([42])
    })

    it('should cleanly purge the canvas context upon component lifecycle destruction (onUnmounted)', async () => {
        const wrapper = mountWithState()
        await flushPromises()
        await nextTick()

        if (sharedCallbacks['NEW']) {
            sharedCallbacks['NEW']({
                headers: { message_subtype: 'configuration' },
                body: JSON.stringify([
                    {
                        configurations: { 'param.threads': 2, 'param.mode': 'auto' },
                        results: { energy: 42 }
                    }
                ])
            })
        }

        vi.advanceTimersByTime(550) 
        await flushPromises()
        await nextTick()

        const chartElement = document.getElementById('my_experiment_id')
        expect(chartElement).not.toBeNull()

        const spyGetElement = vi.spyOn(document, 'getElementById').mockReturnValue(chartElement)

        wrapper.unmount()

        expect(hoistedPlotly.purge).toHaveBeenCalledWith(chartElement)
        spyGetElement.mockRestore()
    })
})