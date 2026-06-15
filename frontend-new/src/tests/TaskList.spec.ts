import { mount, flushPromises } from '@vue/test-utils'

import { describe, it, expect, vi, beforeEach } from 'vitest'

import { createPinia, setActivePinia } from 'pinia'

import { createVuetify } from 'vuetify'

import * as components from 'vuetify/components'

import * as directives from 'vuetify/directives'

import TaskList from '../widgets/task-list/ui/TaskList.vue'

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


    it('NEW event should trigger adding of tasks into the table', async () => {

        vi.useFakeTimers()


        const wrapper = mountComponent()

        await flushPromises()


        const mockTaskData = {

            id: 'task-123',

            config: { param1: 'value1' },

            meta: {

                worker: 'worker-1',

                result: { metric: 42 }

            },

            roundedResults: { metric: 42 }

        }


        const mockEventMessage = {

            headers: { message_subtype: 'task' },

            body: JSON.stringify(mockTaskData)

        }


        eventCallbacks['NEW'](mockEventMessage)

        await flushPromises()


        expect(wrapper.vm.result.length).toBe(0)


        vi.advanceTimersByTime(500)

        await flushPromises()


        expect(wrapper.vm.result.length).toBe(1)

        expect(wrapper.vm.result[0].id).toBe('task-123')


        vi.useRealTimers()

    })
})