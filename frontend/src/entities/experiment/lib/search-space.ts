import type { ParameterSpec } from '../model/experiment.model'

// the prefix of every full parameter name and of every activation category, as main-node names them
export const SEARCH_SPACE_PREFIX = 'Context.SearchSpace'

// a parameter can span a plot axis (contour, rank) if it is numeric or has at least two categories
export function isAxisParameter(spec: ParameterSpec | undefined): boolean {
    if (!spec) {
        return false
    }

    // Float / Integer
    if (
        spec.Type === "FloatHyperparameter" ||
        spec.Type === "IntegerHyperparameter"
    ) {
        return true
    }

    // Nominal / Ordinal
    if (
        spec.Type === "NominalHyperparameter" ||
        spec.Type === "OrdinalHyperparameter"
    ) {
        return (
            Array.isArray(spec.Categories) &&
            spec.Categories.length >= 2
        )
    }

    return false
}
