import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { of, BehaviorSubject, Subject } from 'rxjs'
import { MainEvent } from '../entities/main/model/main.types'
import type { SearchSpaceRegion } from '../entities/experiment/model/experiment.model'

const mockRegions: SearchSpaceRegion[] = [
    {
        ActivationCategory: 'root',
        Parameters: [{
            Name: 'Context.SearchSpace.Algorithm',
            Type: 'NominalHyperparameter',
            Level: 0,
            Categories: ['Context.SearchSpace.Algorithm.A', 'Context.SearchSpace.Algorithm.B'],
            Inactive: 'inactive'
        }]
    },
    {
        ActivationCategory: 'Context.SearchSpace.Algorithm.A',
        Parameters: [{
            Name: 'Context.SearchSpace.Algorithm.A.alpha',
            Type: 'FloatHyperparameter',
            Level: 1,
            Lower: 0,
            Upper: 1,
            Inactive: -1
        }]
    },
    {
        ActivationCategory: 'Context.SearchSpace.Algorithm.B',
        Parameters: [{
            Name: 'Context.SearchSpace.Algorithm.B.gamma',
            Type: 'IntegerHyperparameter',
            Level: 1,
            Lower: 1,
            Upper: 5,
            Inactive: -3
        }]
    }
]

const descriptionMessage = (regions: SearchSpaceRegion[] | undefined, description: object = { Context: { TaskConfiguration: {} } }) => ({
    headers: { message_subtype: 'description' },
    body: JSON.stringify({ experiment_description: description, regions })
})

const mockWatch = vi.fn();
const connectionState$ = new BehaviorSubject<number>(0);

vi.mock('../shared/api/stomp.client.ts', () => ({
    stompClient: {
        connectionState$,
        watch: mockWatch,
        configure: vi.fn(),
        activate: vi.fn(),
    },
}));

vi.mock('@stomp/rx-stomp', () => ({
    RxStomp: vi.fn(() => ({
        configure: vi.fn(),
        activate: vi.fn(),
        connectionState$,
        watch: mockWatch,
    })),
}));

// Import store AFTER mocks are set up
const { useMainEventStore } = await import('../entities/main/model/main.event.store')

describe('useMainEventStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        mockWatch.mockReset()
        // Default: watch() returns an empty Observable
        mockWatch.mockReturnValue(of())
    })

    it('should set isConnected to true when connectionState$ emits 1', () => {
        const store = useMainEventStore()
        connectionState$.next(1)
        expect(store.isConnected).toBe(true)
    })

    it('should set isConnected to false when connectionState$ does not emit 1', () => {
        const store = useMainEventStore()
        connectionState$.next(0)
        expect(store.isConnected).toBe(false)
    })

    it('should return the correct Observable for a given event', () => {
        const mockObservable = of({ body: '{}', headers: {} })
        mockWatch.mockReturnValue(mockObservable)

        const store = useMainEventStore()
        const result = store.onEvent(MainEvent.EXPERIMENT)

        expect(result).toBeDefined()
    })

    it('should return undefined for an unknown event', () => {
        mockWatch.mockReturnValue(of())
        const store = useMainEventStore()
        const result = store.onEvent('unknown' as any)
        expect(result).toBeUndefined()
    })

    it('should subscribe to the EXPERIMENT queue on initEvent', () => {
        const mockMessage = {
            headers: { message_subtype: 'other_subtype' },
            body: '{}'
        }
        mockWatch.mockReturnValue(of(mockMessage))

        const store = useMainEventStore()
        store.initEvent()

        expect(mockWatch).toHaveBeenCalledWith(
            'front_experiment_queue',
            { 'x-message-ttl': '1000' }
        )
    })

    it('should set experiment_description and regions on description message', () => {
        const mockDescription = {
            TaskName: 'TestTask',
            Context: { TaskConfiguration: { TaskName: 'TestTask' } }
        }
        mockWatch.mockReturnValue(of(descriptionMessage(mockRegions, mockDescription)))

        const store = useMainEventStore()
        store.initEvent()

        expect(store.experiment_description).toEqual(mockDescription)
        expect(store.regions).toEqual(mockRegions)
        expect(store.searchspaceReady).toBe(true)
    })

    it('should have no parameters before the description message', () => {
        const store = useMainEventStore()
        expect(store.regions).toEqual([])
        expect(store.specsByName).toEqual({})
    })

    it('should map every parameter of every region by its name', () => {
        mockWatch.mockReturnValue(of(descriptionMessage(mockRegions)))

        const store = useMainEventStore()
        store.initEvent()

        expect(Object.keys(store.specsByName)).toEqual([
            'Context.SearchSpace.Algorithm',
            'Context.SearchSpace.Algorithm.A.alpha',
            'Context.SearchSpace.Algorithm.B.gamma'
        ])
        expect(store.specsByName['Context.SearchSpace.Algorithm.A.alpha']).toEqual(mockRegions[1].Parameters[0])
    })

    it('should replace the description, regions and parameters when a new description arrives', () => {
        const messages = new Subject<any>()
        mockWatch.mockReturnValue(messages)
        const secondDescription = { Context: { TaskConfiguration: { TaskName: 'Second' } } }

        const store = useMainEventStore()
        store.initEvent()
        messages.next(descriptionMessage(mockRegions))
        messages.next(descriptionMessage(mockRegions.slice(0, 1), secondDescription))

        expect(store.experiment_description).toEqual(secondDescription)
        expect(store.regions).toEqual(mockRegions.slice(0, 1))
        expect(Object.keys(store.specsByName)).toEqual(['Context.SearchSpace.Algorithm'])
    })

    it('should leave the regions alone on a message of another subtype', () => {
        const messages = new Subject<any>()
        mockWatch.mockReturnValue(messages)

        const store = useMainEventStore()
        store.initEvent()
        messages.next(descriptionMessage(mockRegions))
        messages.next({ headers: { message_subtype: 'other_subtype' }, body: '{}' })

        expect(store.regions).toEqual(mockRegions)
        expect(store.searchspaceReady).toBe(true)
    })

    describe('a description without regions', () => {
        beforeEach(() => {
            vi.spyOn(console, 'error').mockImplementation(() => {})
        })

        it('should keep the description, report the problem and leave the search space not ready', () => {
            mockWatch.mockReturnValue(of(descriptionMessage(undefined)))

            const store = useMainEventStore()
            store.initEvent()

            expect(store.experiment_description).toEqual({ Context: { TaskConfiguration: {} } })
            expect(store.regions).toEqual([])
            expect(store.specsByName).toEqual({})
            expect(store.searchspaceReady).toBe(false)
            expect(console.error).toHaveBeenCalled()
        })

        it('should clear the regions of the previous description', () => {
            const messages = new Subject<any>()
            mockWatch.mockReturnValue(messages)

            const store = useMainEventStore()
            store.initEvent()
            messages.next(descriptionMessage(mockRegions))
            messages.next(descriptionMessage(undefined))

            expect(store.regions).toEqual([])
            expect(store.specsByName).toEqual({})
            expect(store.searchspaceReady).toBe(false)
        })
    })

    it('should mark the experiment as finished by the final message and as running again by a description', () => {
        const messages = new Subject<any>()
        mockWatch.mockReturnValue(messages)

        const store = useMainEventStore()
        store.initEvent()
        expect(store.experimentFinished).toBe(false)

        messages.next({ headers: { message_subtype: 'configuration' }, body: '{}' })
        expect(store.experimentFinished).toBe(true)

        messages.next(descriptionMessage(mockRegions))
        expect(store.experimentFinished).toBe(false)
    })

    it('should default searchspaceReady to false', () => {
        const store = useMainEventStore()
        expect(store.searchspaceReady).toBe(false)
    })

    it.each([
        ['Infinity', Infinity],
        ['-Infinity', -Infinity],
        ['NaN', NaN]
    ])('should preserve %s in message body', (token, value) => {
        const mockMessage = {
            headers: { message_subtype: 'description' },
            body: `{
                "experiment_description": {"value": ${token}},
                "regions": []
            }`
        }
        mockWatch.mockReturnValue(of(mockMessage))

        const store = useMainEventStore()
        store.initEvent()

        expect(store.experiment_description).toEqual({ value })
    })
})