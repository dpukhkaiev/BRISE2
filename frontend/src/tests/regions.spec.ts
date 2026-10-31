import { describe, it, expect } from 'vitest'
import { regionLabel, trialsWithParameters } from '../entities/experiment/lib/regions'
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
