import type { ParameterSpec, SearchSpaceRegion } from '../../entities/experiment/model/experiment.model'

// the search space as main-node describes it: Algorithm activates either region A (alpha, flag, beta) or region B (gamma)
export const ALGORITHM = 'Context.SearchSpace.Algorithm'
export const ALPHA = 'Context.SearchSpace.Algorithm.A.alpha'
export const FLAG = 'Context.SearchSpace.Algorithm.A.flag'
export const BETA = 'Context.SearchSpace.Algorithm.A.beta'
export const GAMMA = 'Context.SearchSpace.Algorithm.B.gamma'

export const algorithm: ParameterSpec = {
    Name: ALGORITHM,
    Type: 'NominalHyperparameter',
    Level: 0,
    Categories: [`${ALGORITHM}.A`, `${ALGORITHM}.B`],
    Inactive: 'inactive'
}

export const alpha: ParameterSpec = { Name: ALPHA, Type: 'FloatHyperparameter', Level: 1, Lower: 0, Upper: 1, Inactive: -1 }

// a nominal parameter with a single category cannot span a plot axis
export const flag: ParameterSpec = {
    Name: FLAG,
    Type: 'NominalHyperparameter',
    Level: 1,
    Categories: [`${FLAG}.on`],
    Inactive: 'inactive'
}

export const beta: ParameterSpec = { Name: BETA, Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 10, Inactive: -8 }

export const gamma: ParameterSpec = { Name: GAMMA, Type: 'IntegerHyperparameter', Level: 1, Lower: 1, Upper: 5, Inactive: -3 }

export const rootRegion: SearchSpaceRegion = { ActivationCategory: 'root', Parameters: [algorithm] }
export const regionA: SearchSpaceRegion = { ActivationCategory: ALGORITHM + '.A', Parameters: [alpha, flag, beta] }
export const regionB: SearchSpaceRegion = { ActivationCategory: ALGORITHM + '.B', Parameters: [gamma] }

export const regions: SearchSpaceRegion[] = [rootRegion, regionA, regionB]

// every parameter by its full name, as the store builds it from the regions
export const specsByName: Record<string, ParameterSpec> = Object.fromEntries(
    regions.flatMap(region => region.Parameters).map(parameter => [parameter.Name, parameter])
)
