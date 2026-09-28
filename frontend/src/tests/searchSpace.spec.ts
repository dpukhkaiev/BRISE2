import { describe, it, expect } from 'vitest'
import {
    findParameterSpec,
    flattenSearchSpace,
    isContourParameter
} from '../entities/experiment/lib/search-space'
import type { ExperimentDescription } from '../entities/experiment/model/experiment.model'

// Algorithm activates either region A (alpha, beta) or region B (gamma)
const searchSpace = {
    Algorithm: {
        Type: 'NominalHyperparameter',
        Level: 0,
        Categories: ['Context.SearchSpace.Algorithm.A', 'Context.SearchSpace.Algorithm.B'],
        Default: 'Context.SearchSpace.Algorithm.A',
        A: {
            Type: 'Category',
            alpha: { Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 1, Default: 0.5 },
            beta: {
                Type: 'OrdinalHyperparameter',
                Level: 1,
                Categories: ['Context.SearchSpace.Algorithm.A.beta.low', 'Context.SearchSpace.Algorithm.A.beta.high'],
                Default: 'Context.SearchSpace.Algorithm.A.beta.low',
                low: { Type: 'Category' },
                high: { Type: 'Category' }
            }
        },
        B: {
            Type: 'Category',
            gamma: { Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 5, Default: 1 }
        }
    },
    Structure: { Hierarchical: {} }
}

const experiment_description = {
    Context: {
        TaskConfiguration: {},
        SearchSpace: searchSpace
    }
} as unknown as ExperimentDescription

describe('flattenSearchSpace', () => {
    it('names nested parameters by their activation path', () => {
        expect(Object.keys(flattenSearchSpace(searchSpace))).toEqual([
            'Context.SearchSpace.Algorithm',
            'Context.SearchSpace.Algorithm.A.alpha',
            'Context.SearchSpace.Algorithm.A.beta',
            'Context.SearchSpace.Algorithm.B.gamma'
        ])
    })
})

describe('findParameterSpec', () => {
    it('finds a nested parameter by its full name', () => {
        expect(findParameterSpec(experiment_description, 'Context.SearchSpace.Algorithm.B.gamma'))
            .toBe(searchSpace.Algorithm.B.gamma)
    })

    it('finds a top-level parameter by its short name', () => {
        expect(findParameterSpec(experiment_description, 'Algorithm'))
            .toBe(searchSpace.Algorithm)
    })

    it('finds nothing for an unknown parameter', () => {
        expect(findParameterSpec(experiment_description, 'Context.SearchSpace.Algorithm.A.delta'))
            .toBeUndefined()
    })
})

describe('isContourParameter', () => {
    it('accepts numeric parameters and parameters with at least two categories', () => {
        expect(isContourParameter(searchSpace.Algorithm.A.alpha)).toBe(true)
        expect(isContourParameter(searchSpace.Algorithm.A.beta)).toBe(true)
    })

    it('rejects unknown parameters and parameters with a single category', () => {
        expect(isContourParameter(undefined)).toBe(false)
        expect(isContourParameter({ Type: 'NominalHyperparameter', Categories: ['only'] })).toBe(false)
    })
})
