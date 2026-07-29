

export function resolveScenarioLabel(scenario: unknown): string {
    if (!scenario || typeof scenario !== 'object') return 'No scenario data'
    const s = scenario as Record<string, any>

    return (
        s.ws_file ??
        s.Problem ??
        s.InitializationParameters?.instance ??
        JSON.stringify(s) 
    )
}