import type { ParameterSpec } from '../model/experiment.model'

// the prefix of every full parameter name and of every activation category, as main-node names them
export const SEARCH_SPACE_PREFIX = 'Context.SearchSpace'

// the values a parameter takes on a category axis: its categories, or the two bounds of a numeric parameter
export function axisValues(spec: ParameterSpec): Array<string | number> {
    if (spec.Categories) {
        return spec.Categories
    }
    return [spec.Lower, spec.Upper].filter((bound): bound is number => bound !== undefined)
}

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
