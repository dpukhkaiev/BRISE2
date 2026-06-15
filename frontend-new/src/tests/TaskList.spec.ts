import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import TaskList from '../widgets/task-list/ui/TaskList.vue'
import { ref } from 'vue'


globalThis.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
}

// Vuetify setup
const vuetify = createVuetify({ components, directives })

let eventCallbacks: Record<string, (message: any) => void> = {}
const mockUnsubscribe = vi.fn()


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
        NEW: 'NEW'
    },
}))

const mountComponent = (): any => mount(TaskList, {
    global: {
        plugins: [vuetify, createPinia()]
    }
})

describe('TaskList.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        eventCallbacks = {}
    })

    it('NEW RxJS event should be subscribed on mount', () => {
        mountComponent()
        expect(eventCallbacks['NEW']).toBeDefined()
    })

    it('Unmount should end all subscription', () => {
        const wrapper = mountComponent()
        wrapper.unmount()
        expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
    })


})