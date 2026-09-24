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

// eslint-disable-next-line no-unused-vars
let eventCallbacks: Record<string, (message: any) => void>
let mockUnsubscribe: any
let mockExperimentDescription: any
let mockSearchspace: any
const mockExperimentFinished = ref(false)

vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description: mockExperimentDescription,
        searchspace: mockSearchspace,
        experimentFinished: mockExperimentFinished,
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
        FINAL: 'FINAL'
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
        configurations: { 'Context.SearchSpace.N': configValue },
        results: {
            'task id': id,
            owner: 'tester',
            receive: 1,
            result: { x: 1 }
        }
    }])
}

function makeConfigurationPayload(configValue: string, resultValue: number) {
    return JSON.stringify([{
        configurations: { 'Context.SearchSpace.N': configValue },
        results: { x: resultValue }
    }])
}

function makeNaNTaskPayload(id: string, resultValue: number) {
    return `[{
        "run": {"method": "someMethod", "param": {}},
        "configurations": {"Context.SearchSpace.N": NaN},
        "results": {
            "task id": "${id}",
            "owner": "tester",
            "receive": 1,
            "result": {"x": ${resultValue}}
        }
    }]`
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
        mockExperimentFinished.value = false
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
        // one subscription for 'task'/'configuration' events on NEW, plus one each for DEFAULT and FINAL
        expect(mockUnsubscribe).toHaveBeenCalledTimes(3)
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

    it('average result should be computed live from tasks before a configuration event arrives', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1', 'foo')
        })
        vi.advanceTimersByTime(500)
        await flushPromises()

        expect(wrapper.vm.cachedAvg({ 'Context.SearchSpace.N': 'foo' })).toEqual([1])
    })

    it('average result should switch to the backend value once a configuration event is received', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1', 'foo')
        })
        vi.advanceTimersByTime(500)
        await flushPromises()
        expect(wrapper.vm.cachedAvg({ 'Context.SearchSpace.N': 'foo' })).toEqual([1])

        eventCallbacks['NEW']({
            headers: { message_subtype: 'configuration' },
            body: makeConfigurationPayload('foo', 42)
        })
        await flushPromises()

        expect(wrapper.vm.cachedAvg({ 'Context.SearchSpace.N': 'foo' })).toEqual([42])
    })

    it('average result should be computed for a search-space parameter value containing a dot', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeTaskPayload('1', 'Context.SearchSpace.N.N1')
        })
        vi.advanceTimersByTime(500)
        await flushPromises()

        expect(wrapper.vm.cachedAvg({ 'Context.SearchSpace.N': 'Context.SearchSpace.N.N1' })).toEqual([1])
    })

    it('average result should match tasks whose config parameter is NaN', async () => {
        vi.useFakeTimers()
        const wrapper = mountComponent()
        await flushPromises()

        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeNaNTaskPayload('1', 1)
        })
        eventCallbacks['NEW']({
            headers: { message_subtype: 'task' },
            body: makeNaNTaskPayload('2', 3)
        })
        vi.advanceTimersByTime(500)
        await flushPromises()

        // both tasks share the same NaN-valued parameter and must be grouped together,
        // not treated as forever distinct because NaN !== NaN
        expect(wrapper.vm.cachedAvg({ 'Context.SearchSpace.N': NaN })).toEqual([2])
    })
})