import { SEARCH_SPACE_PREFIX } from './search-space'
import type { SearchSpaceRegion } from '../model/experiment.model'

// the top-level region is activated by 'root'; any other region by the category that activates its parameters
export function regionLabel(region: SearchSpaceRegion): string {
    if (!region.ActivationCategory.startsWith(`${SEARCH_SPACE_PREFIX}.`)) {
        return 'Top-level parameters'
    }
    return region.ActivationCategory.slice(SEARCH_SPACE_PREFIX.length + 1)
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
