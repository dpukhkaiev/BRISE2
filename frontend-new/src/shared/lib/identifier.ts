export function cleanIdentifier(s: unknown): string {
  return String(s ?? '').split('.').pop() ?? String(s)
}

// remove context.searchspace prefix
export function normalizeConfigKeys(config: Record<string, any>): Record<string, any> {
  const normalized: Record<string, any> = {}
  Object.entries(config || {}).forEach(([k, v]) => {
    normalized[cleanIdentifier(k)] = v
  })
  return normalized
}