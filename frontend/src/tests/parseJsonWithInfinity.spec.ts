import { describe, it, expect } from 'vitest'
import { parseJsonWithInfinity } from '../shared/lib/parseJsonWithInfinity'

describe('parseJsonWithInfinity', () => {
  it('parses a plain JSON value unchanged', () => {
    expect(parseJsonWithInfinity('{"a": 1, "b": "text"}')).toEqual({ a: 1, b: 'text' })
  })

  it('restores a bare Infinity token to the numeric value', () => {
    expect(parseJsonWithInfinity('{"MaxExpectedValue": Infinity}')).toEqual({ MaxExpectedValue: Infinity })
  })

  it('restores a bare -Infinity token to the numeric value', () => {
    expect(parseJsonWithInfinity('{"MinExpectedValue": -Infinity}')).toEqual({ MinExpectedValue: -Infinity })
  })

  it('restores a bare NaN token to the numeric value', () => {
    expect(parseJsonWithInfinity('{"result": NaN}')).toEqual({ result: NaN })
  })

  it('restores Infinity/-Infinity/NaN tokens nested inside objects', () => {
    const raw = '{"results": {"x": Infinity, "y": -Infinity}, "nested": {"a": NaN}}'
    expect(parseJsonWithInfinity(raw)).toEqual({
      results: { x: Infinity, y: -Infinity },
      nested: { a: NaN }
    })
  })

  it('handles a mix of Infinity, -Infinity, NaN and ordinary values together', () => {
    const raw = '{"a": 1, "b": Infinity, "c": -Infinity, "d": NaN, "e": "text"}'
    expect(parseJsonWithInfinity(raw)).toEqual({ a: 1, b: Infinity, c: -Infinity, d: NaN, e: 'text' })
  })

  it('restores Infinity as a later array element', () => {
    expect(parseJsonWithInfinity('{"a": [0.5, Infinity]}')).toEqual({ a: [0.5, Infinity] })
  })

  it('restores -Infinity as the first array element', () => {
    expect(parseJsonWithInfinity('{"a": [-Infinity, 2]}')).toEqual({ a: [-Infinity, 2] })
  })

  it('restores NaN inside an array', () => {
    expect(parseJsonWithInfinity('{"a": [NaN]}')).toEqual({ a: [NaN] })
  })

  it('round-trips Infinity/-Infinity/NaN inside an array through stringifyWithInfinity', async () => {
    const { stringifyWithInfinity } = await import('../shared/lib/stringifyWithInfinity')
    const value = { a: [Infinity, -Infinity, NaN] }
    expect(parseJsonWithInfinity(stringifyWithInfinity(value))).toEqual(value)
  })
})
