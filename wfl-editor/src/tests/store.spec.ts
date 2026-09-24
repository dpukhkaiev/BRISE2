import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import { useGraphStore } from '../store'

describe('useGraphStore auto-save', () => {
    let setItemSpy: ReturnType<typeof vi.spyOn>

    beforeEach(() => {
        setActivePinia(createPinia())
        localStorage.clear()
        vi.useFakeTimers()
        setItemSpy = vi.spyOn(Storage.prototype, 'setItem')
    })

    afterEach(() => {
        vi.useRealTimers()
        setItemSpy.mockRestore()
    })

    it('coalesces rapid drag-frame position updates into a single write, and still flushes before unload', async () => {
        const store = useGraphStore()
        store.addNode({ id: 'n1', type: 'float', position: { x: 0, y: 0 }, data: {} } as any)
        await nextTick()
        setItemSpy.mockClear() // ignore the write triggered by adding the node

        const node = store.nodes.find((n: any) => n.id === 'n1')

        // simulate ~2s of a node drag: each pointermove is its own event-loop task,
        // ~16ms apart, mutating node.position in place the same way @vue-flow/core does
        for (let frame = 1; frame <= 120; frame++) {
            node.position = { x: frame, y: frame }
            await nextTick()
            vi.advanceTimersByTime(16)
        }

        // the drag hasn't settled yet -- no write should have landed
        expect(setItemSpy).not.toHaveBeenCalled()

        // let the debounce settle after the drag stops
        vi.advanceTimersByTime(500)

        expect(setItemSpy).toHaveBeenCalledTimes(1)
        const settledState = JSON.parse(setItemSpy.mock.calls[0][1] as string)
        expect(settledState.nodes[0].position).toEqual({ x: 120, y: 120 })

        // a change made just before the tab closes must not be lost to the pending debounce
        setItemSpy.mockClear()
        node.position = { x: 999, y: 999 }
        await nextTick()
        expect(setItemSpy).not.toHaveBeenCalled()

        window.dispatchEvent(new Event('beforeunload'))

        expect(setItemSpy).toHaveBeenCalledTimes(1)
        const unloadState = JSON.parse(setItemSpy.mock.calls[0][1] as string)
        expect(unloadState.nodes[0].position).toEqual({ x: 999, y: 999 })
    })
})
