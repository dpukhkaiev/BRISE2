const POS_INFINITY_MARKER = '__BRISE_INFINITY__'
const NEG_INFINITY_MARKER = '__BRISE_NEG_INFINITY__'

// Symmetric to parseJsonWithInfinity
export function stringifyWithInfinity(value: any): string {
   const json = JSON.stringify(value, (_key, val) => {
      if (val === Infinity) return POS_INFINITY_MARKER
      if (val === -Infinity) return NEG_INFINITY_MARKER
      return val
   })

   return json
      .replace(new RegExp(`"${POS_INFINITY_MARKER}"`, 'g'), 'Infinity')
      .replace(new RegExp(`"${NEG_INFINITY_MARKER}"`, 'g'), '-Infinity')
}
