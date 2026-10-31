import type { ParameterSpec } from '../model/experiment.model'

// How charts show a parameter that is not active in a trial. The inactive value of a parameter comes from main-node
// (ParameterSpec.Inactive); this is only its drawing.

export const INACTIVE_LABEL = 'inactive'

// the position of the inactive value on an axis of category indices, next to the first category
export const INACTIVE_INDEX = -1

// the gap between the lower bound of a numeric axis and its inactive position, as a share of the parameter's range;
// the parameter's own inactive value would be a whole range below the bound and squash the real values to half
const GAP_SHARE = 0.1

// the number of labelled ticks between the bounds of a numeric axis, bounds included
const TICK_COUNT = 5

export function inactivePosition(spec: ParameterSpec): number {
    const lower = spec.Lower ?? 0
    const range = (spec.Upper ?? lower) - lower
    return lower - (range > 0 ? range : 1) * GAP_SHARE
}

// the ticks of a numeric axis, with the inactive position labelled in front of the ones between the bounds
export function numericTicksWithInactive(spec: ParameterSpec): { tickvals: number[], ticktext: string[] } {
    const lower = spec.Lower ?? 0
    const range = (spec.Upper ?? lower) - lower
    const isInteger = spec.Type === 'IntegerHyperparameter'

    const tickvals: number[] = [inactivePosition(spec)]
    for (let index = 0; index < TICK_COUNT; index++) {
        const value = lower + (range * index) / (TICK_COUNT - 1)
        tickvals.push(isInteger ? Math.round(value) : value)
    }

    const ticktext = tickvals.map((value, index) => index === 0 ? INACTIVE_LABEL : String(Number(value.toPrecision(4))))
    return { tickvals, ticktext }
}
