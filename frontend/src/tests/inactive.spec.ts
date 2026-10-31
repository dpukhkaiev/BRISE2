import { describe, it, expect } from 'vitest'
import {
    INACTIVE_INDEX,
    INACTIVE_LABEL,
    inactivePosition,
    numericTicksWithInactive
} from '../entities/experiment/lib/inactive'
import type { ParameterSpec } from '../entities/experiment/model/experiment.model'

const numeric = (Type: string, Lower: number, Upper: number): ParameterSpec => ({
    Name: 'Context.SearchSpace.threads',
    Type,
    Level: 0,
    Lower,
    Upper,
    Inactive: Lower - (Upper - Lower)
})

describe('inactive value on a chart', () => {
    it('is labelled and indexed the same way on every chart', () => {
        expect(INACTIVE_LABEL).toBe('inactive')
        expect(INACTIVE_INDEX).toBe(-1)
    })

    it('is placed below the lower bound of a numeric parameter, closer than its inactive value', () => {
        const spec = numeric('FloatHyperparameter', 10, 20)

        expect(inactivePosition(spec)).toBeLessThan(10)
        expect(inactivePosition(spec)).toBeGreaterThan(spec.Inactive as number)
    })

    it('is placed below the lower bound of a numeric parameter with equal bounds', () => {
        expect(inactivePosition(numeric('IntegerHyperparameter', 5, 5))).toBeLessThan(5)
    })

    it('marks its position among the ticks of a numeric axis, ahead of the bounds', () => {
        const spec = numeric('FloatHyperparameter', 0, 8)

        const { tickvals, ticktext } = numericTicksWithInactive(spec)

        expect(tickvals[0]).toBe(inactivePosition(spec))
        expect(ticktext[0]).toBe(INACTIVE_LABEL)
        expect(tickvals.slice(1)).toEqual([0, 2, 4, 6, 8])
        expect(ticktext.slice(1)).toEqual(['0', '2', '4', '6', '8'])
    })

    it('puts whole numbers on the ticks of an integer axis', () => {
        const { tickvals } = numericTicksWithInactive(numeric('IntegerHyperparameter', 1, 10))

        expect(tickvals.slice(1).every(Number.isInteger)).toBe(true)
        expect(tickvals[1]).toBe(1)
        expect(tickvals.at(-1)).toBe(10)
    })
})
