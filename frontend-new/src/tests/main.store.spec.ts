import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { of, BehaviorSubject } from 'rxjs'
import { MainEvent } from '../entities/main/model/main.types'

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

    it('should set experiment_description, searchspace and globalConfig on description message', () => {
        const mockDescription = {
            TaskName: 'TestTask',
            Context: { TaskConfiguration: { TaskName: 'TestTask' } }
        }
        const mockMessage = {
            headers: { message_subtype: 'description' },
            body: JSON.stringify({
                experiment_description: mockDescription,
                searchspace_description: { param: 'value' },
                global_configuration: { config: 'value' }
            })
        }
        mockWatch.mockReturnValue(of(mockMessage))

        const store = useMainEventStore()
        store.initEvent()

        expect(store.experiment_description).toEqual(mockDescription)
        expect(store.searchspace).toEqual({ param: 'value' })
        expect(store.globalConfig).toEqual({ config: 'value' })
    })

    it('should replace Infinity values in message body with null', () => {
        const mockMessage = {
            headers: { message_subtype: 'description' },
            body: `{
                "experiment_description": {"value": Infinity},
                "searchspace_description": {},
                "global_configuration": {}
            }`
        }
        mockWatch.mockReturnValue(of(mockMessage))

        const store = useMainEventStore()
        store.initEvent()

        expect(store.experiment_description).toEqual({ value: null })
    })
})