const POSITIVE_INFINITY_MARKER = '__POSITIVE_INFINITY__'
const NEGATIVE_INFINITY_MARKER = '__NEGATIVE_INFINITY__'
const NAN_MARKER = '__NAN__'

// Symmetric to parseJsonWithInfinity
export function stringifyWithInfinity(value: any, space?: string | number): string {
   const json = JSON.stringify(value, (_key, val) => {
      if (val === Infinity) return POSITIVE_INFINITY_MARKER
      if (val === -Infinity) return NEGATIVE_INFINITY_MARKER
      if (typeof val === 'number' && Number.isNaN(val)) return NAN_MARKER
      return val
   }, space)

   return json
      .replace(new RegExp(`"${POSITIVE_INFINITY_MARKER}"`, 'g'), 'Infinity')
      .replace(new RegExp(`"${NEGATIVE_INFINITY_MARKER}"`, 'g'), '-Infinity')
      .replace(new RegExp(`"${NAN_MARKER}"`, 'g'), 'NaN')
}
