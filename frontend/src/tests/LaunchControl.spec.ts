import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LaunchControl from '../widgets/control-bar/ui/LaunchControl.vue'
import { usePlotStore } from '../entities/main/model/plot.store'
import { ref } from 'vue'

// Vuetify setup
const vuetify = createVuetify({ components, directives })

// Callback variable
let eventCallback: Record<string, Function> = {}

// Mocks
vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description: ref({
            Context: {
                TaskConfiguration: {
                    TaskName: 'Test Experiment',
                    Scenario: { ws_file: 'test.ws' },
                },
            },
        }),
        searchspace: [],
        globalConfig: {},
        isConnected: ref(true),
        onEvent: vi.fn((eventType) => ({
            subscribe: vi.fn((callback) => {
                eventCallback[eventType] = callback
                return { unsubscribe: vi.fn() }
            })
        })),
    })),
    MainClientApi: {
        startMain: vi.fn(),
        stopMain: vi.fn(),
    },
    MainEvent: {
        FINAL: 'FINAL',
    },
}))

vi.mock('../features/download-popup', () => ({
    DownloadPopup: { template: '<div>DownloadPopup</div>' },
}))

const mountComponent = () => mount(LaunchControl, {
    global: {
        plugins: [vuetify, createPinia()]
    }
})

describe('LaunchControl.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
        eventCallback = {} // Reset callbacks
    })

    it('renders experiment name correctly', () => {
        const wrapper = mountComponent()
        expect(wrapper.text()).toContain('Test Experiment')
    })

    it('renders scenario correctly', () => {
        const wrapper = mountComponent()
        expect(wrapper.text()).toContain('test.ws')
    })

    it('Start button is enabled initially', async () => {
        const wrapper = mountComponent()
        await flushPromises()
        const startBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))


        expect(startBtn?.props('disabled')).toBeFalsy()
    })

    it('Stop button is disabled initially', async () => {
        const wrapper = mountComponent()
        await flushPromises()
        const stopBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Stop'))
        expect(stopBtn?.props('disabled')).toBe(true)
    })

    it('calls startMain when Start button is clicked', async () => {
        const { MainClientApi } = await import('../entities/main')
        const wrapper = mountComponent()
        await flushPromises()

        const startBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))

        await startBtn?.trigger('click')
        await flushPromises()

        expect(MainClientApi.startMain).toHaveBeenCalledOnce()
    })

    it('Stop button becomes enabled after Start is clicked', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        const startBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))
        await startBtn?.trigger('click')
        await flushPromises()

        const stopBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Stop'))
        expect(stopBtn?.props('disabled')).toBe(false)
    })

    it('calls stopMain when Stop button is clicked', async () => {
        const { MainClientApi } = await import('../entities/main')
        const wrapper = mountComponent()
        await flushPromises()

        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))?.trigger('click')
        await flushPromises()


        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Stop'))?.trigger('click')
        await flushPromises()

        expect(MainClientApi.stopMain).toHaveBeenCalledOnce()
    })

    it('Download button is not visible initially', async () => {
        const wrapper = mountComponent()
        await flushPromises()
        const saveBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Save'))
        expect(saveBtn).toBeUndefined()
    })

    it('Download button appears after FINAL event is triggered', async () => {
        const wrapper = mountComponent()
        await flushPromises()


        if (eventCallback['FINAL']) {
            eventCallback['FINAL']()
        }
        await flushPromises()


        const saveBtn = wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Save Experiment'))

        expect(saveBtn).toBeDefined()
    })

    it('enables changing the visible charts once an experiment is started', async () => {
        const wrapper = mountComponent()
        await flushPromises()

        // launch control state is module-level: finish any experiment started by previous tests
        eventCallback['FINAL']?.()
        await flushPromises()

        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))?.trigger('click')
        await flushPromises()

        expect(usePlotStore().canChangeVisibleCharts).toBe(true)
    })

    it('disables changing the visible charts when a new experiment description is uploaded', async () => {
        const wrapper = mountComponent()
        await flushPromises()
        const plotStore = usePlotStore()
        plotStore.canChangeVisibleCharts = true

        await wrapper.findComponent({ name: 'VFileInput' })
            .vm.$emit('update:modelValue', new File(['{"Context":{}}'], 'exp.json'))
        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Upload Experiment'))?.trigger('click')

        await vi.waitFor(() => expect(plotStore.canChangeVisibleCharts).toBe(false))
    })
})