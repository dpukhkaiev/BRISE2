import type { ExperimentDescription } from '../model/experiment.model'
import { toFullParamName } from '../../../shared/lib'

const SEARCH_SPACE_PREFIX = 'Context.SearchSpace'

export interface ParameterSpec {
    Type: string
    Categories?: string[]
    Lower?: number
    Upper?: number
    [key: string]: unknown
}

// flattens the nested search space into {full parameter name: description};
// a child parameter of a category is named <parent full name>.<category>.<child>, as on main-node
export function flattenSearchSpace(
    searchSpace: Record<string, any>,
    prefix: string = SEARCH_SPACE_PREFIX
): Record<string, ParameterSpec> {
    const flattened: Record<string, ParameterSpec> = {}

    for (const [name, data] of Object.entries(searchSpace ?? {})) {
        if (name === 'Structure' || typeof data !== 'object' || data === null || !('Type' in data)) {
            continue
        }

        const fullName = `${prefix}.${name}`
        flattened[fullName] = data as ParameterSpec

        for (const [categoryName, categoryData] of Object.entries(data)) {
            if (typeof categoryData === 'object' && categoryData !== null && (categoryData as any).Type === 'Category') {
                Object.assign(
                    flattened,
                    flattenSearchSpace(categoryData as Record<string, any>, `${fullName}.${categoryName}`)
                )
            }
        }
    }

    return flattened
}

// finds the description of a (possibly nested) parameter by its full or top-level name
export function findParameterSpec(
    experiment_description: ExperimentDescription,
    parameter: string
): ParameterSpec | undefined {
    const searchSpace = experiment_description.Context?.SearchSpace as Record<string, any> | undefined
    return flattenSearchSpace(searchSpace ?? {})[toFullParamName(parameter)]
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
