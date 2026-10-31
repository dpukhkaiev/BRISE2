import { describe, it, expect } from 'vitest'
import { axisValues, isAxisParameter } from '../entities/experiment/lib/search-space'
import type { ParameterSpec } from '../entities/experiment/model/experiment.model'

const numeric = (Type: string): ParameterSpec => ({
    Name: 'Context.SearchSpace.Algorithm.A.alpha',
    Type,
    Level: 1,
    Lower: 0,
    Upper: 1,
    Inactive: -1
})

const categorical = (Type: string, categories?: string[]): ParameterSpec => ({
    Name: 'Context.SearchSpace.Algorithm.A.beta',
    Type,
    Level: 1,
    Categories: categories,
    Inactive: 'inactive'
})

const LOW = 'Context.SearchSpace.Algorithm.A.beta.low'
const HIGH = 'Context.SearchSpace.Algorithm.A.beta.high'

describe('isAxisParameter', () => {
    it.each(['FloatHyperparameter', 'IntegerHyperparameter'])('accepts a %s', (type) => {
        expect(isAxisParameter(numeric(type))).toBe(true)
    })

    it.each(['NominalHyperparameter', 'OrdinalHyperparameter'])('accepts a %s with two categories', (type) => {
        expect(isAxisParameter(categorical(type, [LOW, HIGH]))).toBe(true)
    })

    it.each(['NominalHyperparameter', 'OrdinalHyperparameter'])('rejects a %s with a single category', (type) => {
        expect(isAxisParameter(categorical(type, [LOW]))).toBe(false)
    })

    it.each(['NominalHyperparameter', 'OrdinalHyperparameter'])('rejects a %s without categories', (type) => {
        expect(isAxisParameter(categorical(type))).toBe(false)
    })

    it('rejects an unknown parameter and an unknown type', () => {
        expect(isAxisParameter(undefined)).toBe(false)
        expect(isAxisParameter(numeric('Category'))).toBe(false)
    })
})

describe('axisValues', () => {
    it.each(['NominalHyperparameter', 'OrdinalHyperparameter'])('lists the categories of a %s in their order', (type) => {
        expect(axisValues(categorical(type, [LOW, HIGH]))).toEqual([LOW, HIGH])
    })

    it.each(['FloatHyperparameter', 'IntegerHyperparameter'])('lists the two bounds of a %s', (type) => {
        expect(axisValues(numeric(type))).toEqual([0, 1])
    })
})
