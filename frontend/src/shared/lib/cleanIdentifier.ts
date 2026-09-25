export function cleanIdentifier(s: string | number | null | undefined): string {
  const str = String(s ?? '')
  if (str !== '' && !Number.isNaN(Number(str))) {
    return str
  }
  return str.split('.').pop() ?? str
}

// remove Context.SearchSpace prefix from object keys
export function normalizeConfigKeys(config: Record<string, unknown>): Record<string, unknown> {
  const normalized: Record<string, unknown> = {}
  Object.entries(config ?? {}).forEach(([k, v]) => {
    const cleanValue = typeof v === 'string' ? cleanIdentifier(v) : v
    normalized[cleanIdentifier(k)] = cleanValue
  })
  return normalized
}

const SEARCH_SPACE_PREFIX = 'Context.SearchSpace'

export function toFullParamName(name: string): string {
  return name.startsWith(`${SEARCH_SPACE_PREFIX}.`) ? name : `${SEARCH_SPACE_PREFIX}.${name}`
}

