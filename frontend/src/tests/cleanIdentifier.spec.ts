import { describe, it, expect } from 'vitest'
import { cleanIdentifier } from '../shared/lib/cleanIdentifier'

describe('cleanIdentifier', () => {
  it('strips a dotted namespace prefix from an identifier', () => {
    expect(cleanIdentifier('Context.SearchSpace.threads')).toBe('threads')
  })

  it('leaves a plain identifier unchanged', () => {
    expect(cleanIdentifier('threads')).toBe('threads')
  })

  it('leaves an integer value unchanged', () => {
    expect(cleanIdentifier(16)).toBe('16')
  })

  it('does not truncate a decimal value at the decimal point', () => {
    expect(cleanIdentifier(2.4)).toBe('2.4')
    expect(cleanIdentifier('2.4')).toBe('2.4')
  })

  it('leaves a negative decimal value unchanged', () => {
    expect(cleanIdentifier(-3.14)).toBe('-3.14')
  })
})
