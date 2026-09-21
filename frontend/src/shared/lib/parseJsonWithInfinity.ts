const POS_INFINITY_TOKEN = '"__BRISE_INFINITY__"'
const NEG_INFINITY_TOKEN = '"__BRISE_NEG_INFINITY__"'

// main-node emits raw Infinity/-Infinity tokens for unbounded objective boundaries
// (e.g. MinExpectedValue/MaxExpectedValue), which are not valid JSON. Swap them then 
// restore the real Infinity/-Infinity numbers.
export function parseJsonWithInfinity(raw: string): any {
   const clean = raw
      .replace(/:\s*-Infinity/g, `: ${NEG_INFINITY_TOKEN}`)
      .replace(/:\s*Infinity/g, `: ${POS_INFINITY_TOKEN}`)

   return JSON.parse(clean, (_key, value) => {
      if (value === '__BRISE_INFINITY__') return Infinity
      if (value === '__BRISE_NEG_INFINITY__') return -Infinity
      return value
   })
}
