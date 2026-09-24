const POSITIVE_INFINITY_TOKEN = '"__POSITIVE_INFINITY__"'
const NEGATIVE_INFINITY_TOKEN = '"__NEGATIVE_INFINITY__"'
const NAN_TOKEN = '"__NAN__"'

// main-node emits raw Infinity/-Infinity/NaN tokens for unbounded objective boundaries
// (e.g. MinExpectedValue/MaxExpectedValue) and undefined results, which are not valid JSON.
// Swap them then restore the real Infinity/-Infinity/NaN numbers.
export function parseJsonWithInfinity(raw: string): any {
   const clean = raw
      .replace(/:\s*-Infinity/g, `: ${NEGATIVE_INFINITY_TOKEN}`)
      .replace(/:\s*Infinity/g, `: ${POSITIVE_INFINITY_TOKEN}`)
      .replace(/:\s*NaN/g, `: ${NAN_TOKEN}`)

   return JSON.parse(clean, (_key, value) => {
      if (value === '__POSITIVE_INFINITY__') return Infinity
      if (value === '__NEGATIVE_INFINITY__') return -Infinity
      if (value === '__NAN__') return NaN
      return value
   })
}
