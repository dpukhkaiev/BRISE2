export function cleanIdentifier(s: unknown): string {
  return String(s ?? '').split('.').pop() ?? String(s)
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

