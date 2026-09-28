import { describe, it, expect } from 'vitest'
import { regionLabel, trialsWithParameters } from '../entities/experiment/lib/regions'

describe('regionLabel', () => {
    it('labels the region of top-level parameters', () => {
        expect(regionLabel(['Context.SearchSpace.Algorithm', 'Context.SearchSpace.threads']))
            .toBe('Top-level parameters')
    })

    it('labels a nested region by its activation path', () => {
        expect(regionLabel(['Context.SearchSpace.Algorithm.A.alpha', 'Context.SearchSpace.Algorithm.A.beta']))
            .toBe('Algorithm.A')
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

    it('keeps all trials when no parameter is given', () => {
        expect(trialsWithParameters([regionA, regionB], [])).toEqual([regionA, regionB])
    })
})
