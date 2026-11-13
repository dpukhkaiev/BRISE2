import { describe, it, expect } from 'vitest'
import { regionLabel, trialsOfRegion, trialsWithParameters } from '../entities/experiment/lib/regions'
import type { SearchSpaceRegion } from '../entities/experiment/model/experiment.model'

describe('regionLabel', () => {
    const region = (ActivationCategory: string): SearchSpaceRegion => ({ ActivationCategory, Parameters: [] })

    it('labels the region of top-level parameters', () => {
        expect(regionLabel(region('root'))).toBe('Top-level parameters')
    })

    it.each([
        ['Context.SearchSpace.Algorithm.A', 'Algorithm.A'],
        ['Context.SearchSpace.Algorithm.A.beta.high', 'Algorithm.A.beta.high']
    ])('labels the nested region %s by its activation path', (activationCategory, label) => {
        expect(regionLabel(region(activationCategory))).toBe(label)
    })
})

describe('trialsWithParameters', () => {
    const regionA = { configurations: { 'Context.SearchSpace.Algorithm.A.alpha': 0.1, 'Context.SearchSpace.Algorithm.A.beta': 2 } }
    const regionB = { configurations: { 'Context.SearchSpace.Algorithm.B.gamma': 3 } }

    it('keeps only trials in which every given parameter is active', () => {
        expect(trialsWithParameters(
            [regionA, regionB],
            ['Context.SearchSpace.Algorithm.A.alpha', 'Context.SearchSpace.Algorithm.A.beta']
        )).toEqual([regionA])
    })

    it('drops a trial in which only some of the given parameters are active', () => {
        const onlyAlpha = { configurations: { 'Context.SearchSpace.Algorithm.A.alpha': 0.2 } }

        expect(trialsWithParameters(
            [regionA, onlyAlpha],
            ['Context.SearchSpace.Algorithm.A.alpha', 'Context.SearchSpace.Algorithm.A.beta']
        )).toEqual([regionA])
    })

    it('treats a parameter with a falsy value as active', () => {
        const zeroAndEmpty = { configurations: { 'Context.SearchSpace.threads': 0, 'Context.SearchSpace.mode': '' } }

        expect(trialsWithParameters(
            [zeroAndEmpty, regionB],
            ['Context.SearchSpace.threads', 'Context.SearchSpace.mode']
        )).toEqual([zeroAndEmpty])
    })

    it('keeps all trials when no parameter is given', () => {
        expect(trialsWithParameters([regionA, regionB], [])).toEqual([regionA, regionB])
    })

    it('keeps nothing when there are no trials', () => {
        expect(trialsWithParameters([], ['Context.SearchSpace.Algorithm.A.alpha'])).toEqual([])
    })
})

describe('trialsOfRegion', () => {
    const alpha = { Name: 'Context.SearchSpace.Algorithm.A.alpha', Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 1, Inactive: -1 }
    const beta = { Name: 'Context.SearchSpace.Algorithm.A.beta', Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 10, Inactive: -8 }
    const regionA = { ActivationCategory: 'Context.SearchSpace.Algorithm.A', Parameters: [alpha, beta] }

    const both = { configurations: { 'Context.SearchSpace.Algorithm.A.alpha': 0.1, 'Context.SearchSpace.Algorithm.A.beta': 2 } }
    const onlyAlpha = { configurations: { 'Context.SearchSpace.Algorithm.A.alpha': 0.2 } }
    const otherRegion = { configurations: { 'Context.SearchSpace.Algorithm.B.gamma': 3 } }

    it('keeps the trials in which a parameter of the region is active, whichever it is', () => {
        expect(trialsOfRegion([both, onlyAlpha, otherRegion], regionA)).toEqual([both, onlyAlpha])
    })

    it('drops the trials of other regions', () => {
        expect(trialsOfRegion([otherRegion], regionA)).toEqual([])
    })

    it('keeps every trial for a region without parameters that a trial must have', () => {
        const root = { ActivationCategory: 'root', Parameters: [{ ...alpha, Name: 'Context.SearchSpace.Algorithm' }] }
        const trial = { configurations: { 'Context.SearchSpace.Algorithm': 'Context.SearchSpace.Algorithm.A' } }

        expect(trialsOfRegion([trial, trial], root)).toEqual([trial, trial])
    })
})
