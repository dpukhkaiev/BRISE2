const SEARCH_SPACE_PREFIX = 'Context.SearchSpace'

// a region is the list of full names of sibling parameters activated by the same parent category,
// so the activation path of a region is the full name of any of its parameters without the last segment
export function regionLabel(regionParameters: string[]): string {
    const parameter = regionParameters[0] ?? ''
    const activationPath = parameter.slice(0, parameter.lastIndexOf('.'))

    if (!activationPath.startsWith(`${SEARCH_SPACE_PREFIX}.`)) {
        return 'Top-level parameters'
    }
    return activationPath.slice(SEARCH_SPACE_PREFIX.length + 1)
}

// keeps only the trials in which every given parameter was active
export function trialsWithParameters<T extends { configurations: Record<string, unknown> }>(
    trials: T[],
    parameters: string[]
): T[] {
    return trials.filter(trial =>
        parameters.every(parameter => trial.configurations[parameter] !== undefined)
    )
}
