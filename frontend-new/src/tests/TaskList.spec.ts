import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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

const vuetify = createVuetify({ components, directives })

let eventCallbacks: Record<string, (message: any) => void>
let mockUnsubscribe: any
let mockExperimentDescription: any
let mockSearchspace: any

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

function makeTaskPayload(id: string, configValue = 'foo') {
    return JSON.stringify([{
        run: { method: 'someMethod', param: {} },
        configurations: { ws_file: configValue },
        results: {
            'task id': id,
            owner: 'tester',
            receive: 1,
            result: { x: 1 }
        }
    }])
}

describe('TaskList.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        
        eventCallbacks = {}
        mockUnsubscribe = vi.fn()
        mockSearchspace = ref([])
        mockExperimentDescription = ref({
            Context: { TaskConfiguration: { TaskName: 'TestExperiment' } }
        })
    })

    afterEach(() => {
        vi.useRealTimers()
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

    it('new tasks should be added to result after the interval', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1')
        })

        expect(wrapper.vm.result.length).toBe(0)

        vi.advanceTimersByTime(500)
        await flushPromises()

        expect(wrapper.vm.result.length).toBe(1)
    })

    it('batching should take 20 tasks per interval', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        for (let i = 0; i < 25; i++) {
            eventCallbacks['NEW']({
                headers: { message_subtype: 'task' },
                body: makeTaskPayload(String(i))
            })
        }

        vi.advanceTimersByTime(500)
        await flushPromises()
        expect(wrapper.vm.result.length).toBe(20)

        vi.advanceTimersByTime(500)
        await flushPromises()
        expect(wrapper.vm.result.length).toBe(25)
    })

    it('should reset result on experiment change', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1')
        })
        vi.advanceTimersByTime(500)
        await flushPromises()
        expect(wrapper.vm.result.length).toBe(1)

        mockExperimentDescription.value = { Context: { TaskConfiguration: { TaskName: 'NeuesExperiment' } } }
        await flushPromises()

        expect(wrapper.vm.result.length).toBe(0)
    })

    it('filter should reduce visible tasks', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1', 'foo')
        })
        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('2', 'bar')
        })

        vi.advanceTimersByTime(500)
        await flushPromises()
        expect(wrapper.vm.result.length).toBe(2)

        const input = wrapper.find('input')
        expect(input.exists()).toBe(true)

        // simulate the filter behaviour through the function
        wrapper.vm.applyFilter('foo')
        await flushPromises()

       // check the filtered result
        expect(wrapper.vm.filteredResult.length).toBe(1)
    })
})