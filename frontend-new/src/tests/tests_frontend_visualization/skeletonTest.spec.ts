import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import { Skeleton } from '../../widgets/charts/skeleton-chart'
import type { PointExp } from '../../entities/main/model/plot.store'
import type { ExperimentDescription } from '../../entities/experiment/model/experiment.model'


let eventCallbacks: Record<string, Function> = {}

const defaultExperimentDescription: ExperimentDescription = {
    Context: {
        TaskConfiguration: {
            MaxTasksPerConfiguration: 1,
            MaxTimeToRunTask: 60,
            RepeaterDecisionFunction: '',
            Objectives: {
                runtime: {
                    Name: 'runtime',
                    DataType: 'float',
                    Minimization: true,
                    MinExpectedValue: 0,
                    MaxExpectedValue: Infinity
                }
            },
            ObjectivesDataTypes: ['float'],
            ObjectivesPriorities: [1],
            TaskName: 'testTask',
            Scenario: {
                ws_file: 'test.ws'
            },
            TimeUnit: 'seconds'
        },
        SearchSpace: {}
    },

    PlotSelection: {
        Plot: {
            OptimizationHistory: {},
            RankPlot: {},
            SlicePlot: {},
            EDFPlot: {}
        }
    }
}

const mockStore = {
    experiment_description: ref(defaultExperimentDescription),

    globalConfig: ref({}),

    onEvent: vi.fn((eventType) => ({
        subscribe: vi.fn((callback) => {
            eventCallbacks[eventType] = callback

            return {
                unsubscribe: vi.fn()
            }
        })
    }))
}

const mockPlotStore = {
    allRes: ref<PointExp[]>([]),
    selected: ref<Record<string, boolean>>({}),
    visibleCharts: ref<string[]>([])
}

vi.mock('../../entities/main', () => ({
    useMainEventStore: vi.fn(() => mockStore),

    MainEvent: {
        DEFAULT: 'DEFAULT',
        NEW: 'NEW',
        FINAL: 'FINAL'
    }
}))

vi.mock('../../entities/main/model/plot.store', () => ({
    usePlotStore: vi.fn(() => mockPlotStore)
}))

describe('Skeleton.vue', () => {

    beforeEach(() => {
        setActivePinia(createPinia())

        vi.clearAllMocks()

        eventCallbacks = {}

        mockPlotStore.allRes.value = []
        mockPlotStore.selected.value = {}
        mockPlotStore.visibleCharts.value = []
    })

    const mountComponent = () => {
        return mount(Skeleton, {
            global: {
                plugins: [createPinia()]
            }
        })
    }

    it('registers event listeners', async () => {
        mountComponent()

        await flushPromises()

        expect(mockStore.onEvent).toHaveBeenCalled()

        expect(eventCallbacks['DEFAULT']).toBeDefined()
        expect(eventCallbacks['NEW']).toBeDefined()
        expect(eventCallbacks['FINAL']).toBeDefined()
    })

    it('stores results from DEFAULT event in plotStore.allRes', async () => {
        mount(Skeleton)

        await flushPromises()

        expect(eventCallbacks['DEFAULT']).toBeDefined()

        eventCallbacks['DEFAULT']({
            headers: {
                message_subtype: 'configuration'
            },
            body: JSON.stringify([
                {
                    configurations: {
                        frequency: 50,
                        threads: 4
                    },
                    results: [123.4]
                }
            ])
        })

        await flushPromises()

        expect(mockPlotStore.allRes.value).toEqual([
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4],
                time: expect.any(String),
                'measured points': 1
            }
        ])
    })

    it('stores results from NEW event in plotStore.allRes', async () => {
        mount(Skeleton)

        await flushPromises()

        expect(eventCallbacks['NEW']).toBeDefined()

        eventCallbacks['NEW']({
            headers: {
                message_subtype: 'configuration'
            },
            body: JSON.stringify([
                {
                    configurations: {
                        frequency: 50,
                        threads: 4
                    },
                    results: [123.4]
                }
            ])
        })

        await flushPromises()

        expect(mockPlotStore.allRes.value).toEqual([
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4],
                time: expect.any(String),
                'measured points': 1
            }
        ])
    })

    it('stores results from FINAL event in plotStore.allRes', async () => {
        mount(Skeleton)

        await flushPromises()

        expect(eventCallbacks['FINAL']).toBeDefined()

        eventCallbacks['FINAL']({
            headers: {
                message_subtype: 'configuration'
            },
            body: JSON.stringify([
                {
                    configurations: {
                        frequency: 50,
                        threads: 4
                    },
                    results: [123.4]
                }
            ])
        })

        await flushPromises()

        expect(mockPlotStore.allRes.value).toEqual([
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4],
                time: expect.any(String),
                'measured points': 1
            }
        ])
    })

    it('stores selected plots in experiment description in plotStore.selected and in plotStore.visibleCharts', async () => {
        mount(Skeleton)

        await flushPromises()

        expect(mockPlotStore.selected.value).toEqual({
            'Optimization History': true,
            'Parallel Coordinates': false,
            'Rank Plot': true,
            'Hyperparameter Importances': false,
            'Slice Plot': true,
            'Contour Plot': false,
            'Pareto Front': false,
            'EDF Plot': true
        })
        expect(mockPlotStore.visibleCharts.value).toEqual(
            ['Optimization History', 'Rank Plot', 'Slice Plot', 'EDF Plot']
        )
    })

    it('should reset allRes, selected and visibleCharts when a new experiment description arrives', async () => {
        const wrapper = mount(Skeleton)

        await flushPromises()

        mockPlotStore.allRes.value = [
            {
                configurations: {
                    frequency: 50,
                    threads: 4
                },
                results: [123.4],
                time: '10m 20s',
                'measured points': 1
            }
        ]

        mockPlotStore.selected.value = {
            'Optimization History': true,
            'Parallel Coordinates': false,
            'Rank Plot': true,
            'Hyperparameter Importances': false,
            'Slice Plot': true,
            'Contour Plot': false,
            'Pareto Front': false,
            'EDF Plot': true
        }

        mockPlotStore.visibleCharts.value = [
            'Optimization History',
            'Rank Plot',
            'Slice Plot',
            'EDF Plot'
        ]

        mockStore.experiment_description.value = {
            Context: {
                TaskConfiguration: {
                    MaxTasksPerConfiguration: 1,
                    MaxTimeToRunTask: 60,
                    RepeaterDecisionFunction: '',
                    Objectives: {
                        runtime: {
                            Name: 'runtime',
                            DataType: 'float',
                            Minimization: true,
                            MinExpectedValue: 0,
                            MaxExpectedValue: Infinity
                        }
                    },
                    ObjectivesDataTypes: ['float'],
                    ObjectivesPriorities: [1],
                    TaskName: 'testTask',
                    Scenario: {
                        ws_file: 'test.ws'
                    },
                    TimeUnit: 'seconds'
                },
                SearchSpace: {}
            },
            PlotSelection: {
                Plot: {
                    OptimizationHistory: {},
                    ParallelCoordinates: {},
                    ParetoFront: {}
                }
            }
        }

        await flushPromises()
        await wrapper.vm.$nextTick()

        expect(mockPlotStore.allRes.value).toEqual([])

        expect(mockPlotStore.selected.value).toEqual({
            'Optimization History': true,
            'Parallel Coordinates': true,
            'Rank Plot': false,
            'Hyperparameter Importances': false,
            'Slice Plot': false,
            'Contour Plot': false,
            'Pareto Front': true,
            'EDF Plot': false
        })

        expect(mockPlotStore.visibleCharts.value).toEqual([
            'Optimization History',
            'Parallel Coordinates',
            'Pareto Front'
        ])
    })
})