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

// the store is shared by all mounts of a test, as the real one is
const runningExperiment = {
    Context: {
        TaskConfiguration: {
            TaskName: 'Test Experiment',
            Scenario: { ws_file: 'test.ws' },
        },
    },
}
const experimentDescription = ref<any>(runningExperiment)
const rawProductConfiguration = ref<any>(null)
const searchspaceReady = ref(true)

// Mocks
vi.mock('../entities/main', () => ({
    useMainEventStore: vi.fn(() => ({
        experiment_description: experimentDescription,
        raw_product_configuration: rawProductConfiguration,
        searchspaceReady,
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
        experimentDescription.value = runningExperiment
        rawProductConfiguration.value = null
        searchspaceReady.value = true
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
        eventCallback['FINAL']?.()
        await flushPromises()

        await wrapper.findComponent({ name: 'VFileInput' })
            .vm.$emit('update:modelValue', new File(['{"Context":{}}'], 'exp.json'))
        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Upload Experiment'))?.trigger('click')

        await vi.waitFor(() => expect(plotStore.canChangeVisibleCharts).toBe(false))
    })

    it('does not allow an upload while an experiment is running', async () => {
        const wrapper = mountComponent()
        eventCallback['FINAL']?.()
        await flushPromises()
        const uploadButton = () => wrapper.findAllComponents({ name: 'VBtn' }).find(b => b.text().includes('Upload Experiment'))
        const fileInput = () => wrapper.findComponent({ name: 'VFileInput' })
        expect(uploadButton()?.props('disabled')).toBeFalsy()

        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))?.trigger('click')
        await flushPromises()

        expect(uploadButton()?.props('disabled')).toBe(true)
        expect(fileInput().props('disabled')).toBe(true)

        eventCallback['FINAL']?.()
        await flushPromises()

        expect(uploadButton()?.props('disabled')).toBe(false)
        expect(fileInput().props('disabled')).toBe(false)
    })

    describe('with an uploaded product configuration', () => {
        const uploaded = {
            Context: {
                TaskConfiguration: { TaskName: 'Uploaded Experiment', Scenario: { ws_file: 'uploaded.ws' } },
                SearchSpace: { N0: { Type: 'NominalHyperparameter' } }
            }
        }

        const upload = async (wrapper: ReturnType<typeof mountComponent>, content: object) => {
            // launch control state is module-level, and an upload is only possible while no experiment runs
            eventCallback['FINAL']?.()
            await flushPromises()
            await wrapper.findComponent({ name: 'VFileInput' })
                .vm.$emit('update:modelValue', new File([JSON.stringify(content)], 'exp.json'))
            await wrapper.findAllComponents({ name: 'VBtn' })
                .find(b => b.text().includes('Upload Experiment'))?.trigger('click')
        }

        const clickStart = async (wrapper: ReturnType<typeof mountComponent>) => {
            await wrapper.findAllComponents({ name: 'VBtn' })
                .find(b => b.text().includes('Start'))?.trigger('click')
            await flushPromises()
        }

        it('keeps the uploaded file apart from the description of the running experiment', async () => {
            const wrapper = mountComponent()

            await upload(wrapper, uploaded)

            await vi.waitFor(() => expect(rawProductConfiguration.value).toEqual(uploaded))
            expect(experimentDescription.value).toEqual(runningExperiment)
        })

        it('shows the name and scenario of the uploaded file', async () => {
            rawProductConfiguration.value = uploaded
            const wrapper = mountComponent()

            expect(wrapper.text()).toContain('Uploaded Experiment')
            expect(wrapper.text()).toContain('uploaded.ws')
            expect(wrapper.text()).not.toContain('Test Experiment')
        })

        it('clears the chart data and the chart selection of the previous experiment', async () => {
            const wrapper = mountComponent()
            const plotStore = usePlotStore()
            plotStore.allRes = [{ configurations: {}, results: {}, time: '1m 0s', 'measured points': 1 }]
            plotStore.solution = { configurations: {}, results: {}, time: '1m 0s', 'measured points': 1 }
            plotStore.selected['Slice Plot'] = true
            plotStore.visibleCharts = ['Slice Plot']

            await upload(wrapper, uploaded)

            await vi.waitFor(() => expect(plotStore.allRes).toEqual([]))
            expect(plotStore.solution).toBeNull()
            expect(plotStore.visibleCharts).toEqual([])
            expect(Object.values(plotStore.selected).some(isSelected => isSelected)).toBe(false)
        })

        it('marks the search space as not ready until main-node describes it', async () => {
            const wrapper = mountComponent()

            await upload(wrapper, uploaded)

            await vi.waitFor(() => expect(searchspaceReady.value).toBe(false))
        })

        it('starts with the uploaded file, including its search space', async () => {
            const { MainClientApi } = await import('../entities/main')
            rawProductConfiguration.value = uploaded
            const wrapper = mountComponent()
            eventCallback['FINAL']?.()
            await flushPromises()

            await clickStart(wrapper)

            expect(MainClientApi.startMain).toHaveBeenLastCalledWith(uploaded)
        })

        it('starts with the uploaded file again after a description event replaced the running description', async () => {
            const { MainClientApi } = await import('../entities/main')
            rawProductConfiguration.value = uploaded
            const wrapper = mountComponent()
            eventCallback['FINAL']?.()
            await flushPromises()
            await clickStart(wrapper)
            eventCallback['FINAL']?.()
            await flushPromises()

            // main-node describes the running experiment without its search space
            experimentDescription.value = { Context: { TaskConfiguration: uploaded.Context.TaskConfiguration } }
            await flushPromises()
            await clickStart(wrapper)

            expect(MainClientApi.startMain).toHaveBeenCalledTimes(2)
            expect(MainClientApi.startMain).toHaveBeenLastCalledWith(uploaded)
        })
    })

    it('starts the default experiment when no file was uploaded', async () => {
        const { MainClientApi } = await import('../entities/main')
        const wrapper = mountComponent()
        eventCallback['FINAL']?.()
        await flushPromises()

        await wrapper.findAllComponents({ name: 'VBtn' })
            .find(b => b.text().includes('Start'))?.trigger('click')
        await flushPromises()

        expect(MainClientApi.startMain).toHaveBeenLastCalledWith(null)
    })
})
