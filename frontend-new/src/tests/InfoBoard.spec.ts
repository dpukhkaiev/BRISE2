import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import InfoBoard from '../widgets/info-board/ui/InfoBoard.vue'
import { ref } from 'vue'

// Vuetify setup
const vuetify = createVuetify({ components, directives })

// record for storing event callbacks to trigger them in test later
let eventCallbacks: Record<string, (message: any) => void> = {}
const mockUnsubscribe = vi.fn()

// reactive variable defined outside for manipulating 
const mockExperimentDescription = ref({
    Context: { TaskConfiguration: { TaskName: 'TestExperiment' } }
})
const mockSearchspace = ref([])

// Mocks
vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description: mockExperimentDescription,
        searchspace: mockSearchspace,
        onEvent: vi.fn((eventType) => ({
            subscribe: vi.fn((callback) => {
                eventCallbacks[eventType] = callback
                return { unsubscribe: mockUnsubscribe }
            })
        })),
    })),
    MainEvent: {
        NEW: 'NEW',
        DEFAULT: 'DEFAULT',
        FINAL: 'FINAL',
        LOG: 'LOG',
        PREDICTIONS: 'PREDICTIONS',
    },
}))

const mountComponent = (): any => mount(InfoBoard, {
    global: {
        plugins: [vuetify, createPinia()]
    }
})

describe('InfoBoard.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        eventCallbacks = {}

        Object.defineProperty(window, 'visualViewport', {
            writable: true,
            configurable: true,
            value: {
                width: 1024,
                height: 768,
                offsetLeft: 0,
                offsetTop: 0,
                pageLeft: 0,
                pageTop: 0,
                scale: 1,
                addEventListener: vi.fn(),
                removeEventListener: vi.fn(),
            },
        })
    })

    it('all RxJS events should be subscribed on mount', () => {
        mountComponent()

        expect(eventCallbacks['DEFAULT']).toBeDefined()
        expect(eventCallbacks['FINAL']).toBeDefined()
        expect(eventCallbacks['LOG']).toBeDefined()
        expect(eventCallbacks['NEW']).toBeDefined()
        expect(eventCallbacks['PREDICTIONS']).toBeDefined()
    })

    it('Unmount should end all subscription', () => {
        const wrapper = mountComponent()
        wrapper.unmount()

        expect(mockUnsubscribe).toHaveBeenCalledTimes(5)
    })

    it('Messages should be add to news and snackbar is active when LOG Event', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        const mockLogMessage = {
            headers: { message_subtype: 'info' },
            body: JSON.stringify('Server connection is successfully set')
        }

        eventCallbacks['LOG'](mockLogMessage)
        await flushPromises()

        expect((wrapper.vm as any).snackbarMsg).toBe('Server connection is successfully set')
        expect((wrapper.vm as any).snackbar).toBe(true)


        const lastNewsIndex = (wrapper.vm as any).news.length - 1
        expect((wrapper.vm as any).news[lastNewsIndex].message).toBe('Server connection is successfully set')
    })

    it('pushNews limits news array to max 30 messages', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        for (let i = 1; i <= 35; i++) {
            eventCallbacks['LOG']({
                headers: { message_subtype: 'info' },
                body: JSON.stringify(`message ${i}`)
            })
        }
        await flushPromises()

        expect((wrapper.vm as any).news.length).toBe(30)
        expect((wrapper.vm as any).news[0].message).toBe('message 6')
    })

    it('FINAL event defines the Solution space', async () => {
        const wrapper = mountComponent()

        wrapper.vm.default_configuration = {
            results: { metric: 100 }
        }

        const mockFinalMessage = {
            headers: { message_subtype: 'configuration' },
            body: JSON.stringify([{
                configurations: { param1: 'value1' },
                results: [10],
                performed_measurements: 5
            }])
        }

        eventCallbacks['FINAL'](mockFinalMessage)
        await flushPromises()

        expect(wrapper.vm.solutionState.solution).toBeDefined()
    })

    it('experiment_description change refreshes the state', async () => {
        const wrapper = mountComponent()
        await flushPromises()


        wrapper.vm.news = [{ time: Date.now(), message: 'some old message' }];
        (wrapper.vm as any).solutionState = { solution: {}, configWithNones: 'test', result: 'test' } as any


        mockExperimentDescription.value = {
            Context: { TaskConfiguration: { TaskName: 'new_experiment' } }
        } as any

        await flushPromises()


        expect(wrapper.vm.news.length).toBe(1)
        expect(wrapper.vm.news[0].message).toContain("The main configurations of the experiment are obtained")
        expect(wrapper.vm.solutionState.solution).toBeUndefined()
    })

    it('% are correctly formatted with formatPercent', () => {
        const wrapper = mountComponent()
        const result = wrapper.vm.formatPercent(85.3456)

        expect(result).toBe('85.35')
    })
})