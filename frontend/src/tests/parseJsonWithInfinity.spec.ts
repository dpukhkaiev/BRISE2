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

  it('restores Infinity/-Infinity/NaN tokens nested inside objects (main-node results are always an object, never a bare array)', () => {
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
})
