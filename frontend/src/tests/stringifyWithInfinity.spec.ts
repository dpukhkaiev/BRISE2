import { describe, it, expect } from 'vitest'
import { stringifyWithInfinity } from '../shared/lib/stringifyWithInfinity'

describe('stringifyWithInfinity', () => {
  it('stringifies a plain JSON value unchanged', () => {
    expect(stringifyWithInfinity({ a: 1, b: 'text' })).toBe('{"a":1,"b":"text"}')
  })

  it('emits a bare Infinity token instead of null', () => {
    expect(stringifyWithInfinity({ MaxExpectedValue: Infinity })).toBe('{"MaxExpectedValue":Infinity}')
  })

  it('emits a bare -Infinity token instead of null', () => {
    expect(stringifyWithInfinity({ MinExpectedValue: -Infinity })).toBe('{"MinExpectedValue":-Infinity}')
  })

  it('emits a bare NaN token instead of null', () => {
    expect(stringifyWithInfinity({ result: NaN })).toBe('{"result":NaN}')
  })

  it('emits Infinity/-Infinity/NaN tokens nested inside arrays and objects', () => {
    const value = { results: [Infinity, -Infinity, NaN], nested: { a: NaN } }
    expect(stringifyWithInfinity(value)).toBe('{"results":[Infinity,-Infinity,NaN],"nested":{"a":NaN}}')
  })

  it('round-trips Infinity/-Infinity/NaN through parseJsonWithInfinity', async () => {
    const { parseJsonWithInfinity } = await import('../shared/lib/parseJsonWithInfinity')
    const value = { a: Infinity, b: -Infinity, c: NaN, d: 1, e: 'text' }
    expect(parseJsonWithInfinity(stringifyWithInfinity(value))).toEqual(value)
  })

  it('preserves pretty-printing when a space argument is given', () => {
    const result = stringifyWithInfinity({ a: Infinity }, 2)
    expect(result).toBe('{\n  "a": Infinity\n}')
  })
})
