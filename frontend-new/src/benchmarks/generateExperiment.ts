import type { PointExp } from "../entities/main/model/plot.store"
import type { ExperimentDescription } from "../entities/experiment/model/experiment.model"

export type ParameterType =
    | "FloatHyperparameter"
    | "IntegerHyperparameter"
    | "NominalHyperparameter"
    | "OrdinalHyperparameter"

export interface BenchmarkConfig {
    numTrials: number;
    numParameters: number;
    numObjectives: number;
    seed?: number;
}

export interface BenchmarkTrial {
    configurations: Record<string, string | number>
    results: Record<string, number>
}

export interface BenchmarkParameter {
    Name: string
    Type: ParameterType
    Values?: Array<string | number>
    LowerBound?: number
    UpperBound?: number
}

export interface BenchmarkExperimentDescription {
    Context: {
        SearchSpace: Record<string, BenchmarkParameter>

        TaskConfiguration: {
            TaskName: string
            Objectives: Record<
                string,
                {
                    Name: string
                    DataType: "float"
                    Minimization: boolean
                }
            >
        }
    }
}

export interface GeneratedExperiment {
    experimentDescription: ExperimentDescription
    allRes: PointExp[]
}

function stringToNumber(value: string): number {
    let hash = 0

    for (let i = 0; i < value.length; i++) {
        hash = (hash << 5) - hash + value.charCodeAt(i)
        hash |= 0
    }

    return Math.abs(hash % 100) / 100
}

function createExperimentDescription(
    searchSpace: Record<string, any>,
    objectives: Record<string, any>
): ExperimentDescription {
    return {
        Context: {
            SearchSpace: searchSpace,

            TaskConfiguration: {
                TaskName: "benchmark",
                Objectives: objectives
            }
        }
    } as ExperimentDescription;
}

function generateParameterValue(
    parameter: BenchmarkParameter,
    random: () => number
): string | number {
    switch (parameter.Type) {
        case "FloatHyperparameter": {
            const lower = parameter.LowerBound ?? 0
            const upper = parameter.UpperBound ?? 1

            return lower + random() * (upper - lower)
        }

        case "IntegerHyperparameter": {
            const lower = parameter.LowerBound ?? 0
            const upper = parameter.UpperBound ?? 1

            return lower + Math.floor(random()) * (upper - lower)
        }

        case "OrdinalHyperparameter": {
            if (!parameter.Values || parameter.Values.length === 0) {
                throw new Error(
                    `Ordinal parameter ${parameter.Name} has no values`
                )
            }

            const index = Math.floor(
                random() * parameter.Values.length
            )

            return parameter.Values[index]
        }

        case "NominalHyperparameter": {
            if (!parameter.Values || parameter.Values.length === 0) {
                throw new Error(
                    `Nominal parameter ${parameter.Name} has no values`
                )
            }

            const index = Math.floor(
                random() * parameter.Values.length
            )

            return parameter.Values[index]
        }
    }
}

function generateObjectiveValue(
    configurations: Record<string, string | number>,
    random: () => number
): number {
    let value = 0

    const parameterValues = Object.values(configurations)

    parameterValues.forEach((parameter) => {
        let numericValue: number

        if (typeof parameter === "number") {
            numericValue = parameter / 100
        } else {
            numericValue = stringToNumber(parameter)
        }
    })

    value += (random() - 0.5) * 0.1

    return value
}

function createSeededRandom(seed: number): () => number {
    let state = seed >>> 0

    return () => {
        state += 0x6D2B79F5

        let t = state
        t = Math.imul(t ^ (t >>> 15), t | 1)
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61)

        return (
            ((t ^ (t >>> 14)) >>> 0) /
            4294967296
        )
    }
}

export function generateExperiment(
    config: BenchmarkConfig
): GeneratedExperiment {
    const {
        numTrials,
        numParameters,
        numObjectives,
        seed = 42
    } = config

    if (numTrials < 1) {
        throw new Error("numTrials must be at least 1")
    }

    if (numParameters < 1) {
        throw new Error("numParameters must be at least 1")
    }

    if (numObjectives < 1) {
        throw new Error("numObjectives must be at least 1")
    }

    const random = createSeededRandom(seed)

    const searchSpace: Record<string, any> = {};
    const objectives: Record<string, any> = {};

    for (let i = 0; i < numParameters; i++) {
        const parameterName = `parameter${i + 1}`
        const type = i % 4

        if (type === 0) {
            searchSpace[parameterName] = {
                Name: parameterName,
                Type: "FloatHyperparameter",
                LowerBound: 0,
                UpperBound: 100
            }
        } else if (type === 1) {
            searchSpace[parameterName] = {
                Name: parameterName,
                Type: "IntegerHyperparameter",
                LowerBound: 0,
                UpperBound: 100
            }
        }
        else if (type === 2) {
            searchSpace[parameterName] = {
                Name: parameterName,
                Type: "OrdinalHyperparameter",
                Values: [
                    1,
                    2,
                    4,
                    8,
                    16,
                    32
                ]
            }
        } else {
            searchSpace[parameterName] = {
                Name: parameterName,
                Type: "NominalHyperparameter",
                Values: [
                    "value1",
                    "value2",
                    "value3",
                    "value4"
                ]
            }
        }
    }


    for (let i = 0; i < numObjectives; i++) {
        const objectiveName = `objective${i + 1}`

        objectives[objectiveName] = {
            Name: objectiveName,
            DataType: "float",
            Minimization: i % 2 === 0
        }
    }

    const allRes: PointExp[] = []

    for (let trialIndex = 0; trialIndex < numTrials; trialIndex++) {
        const configurations: Record<string, string | number> = {}

        for (const parameter of Object.values(searchSpace)) {
            configurations[parameter.Name] =
                generateParameterValue(parameter, random)
        }

        const results: Record<string, number> = {}

        for (const objective of Object.values(objectives)) {
            results[objective.Name] =
                generateObjectiveValue(
                    configurations,
                    random
                )
        }

        allRes.push({
            configurations,
            results,
            time: "1m 10s",
            "measured points": 1
        })
    }

    const experimentDescription =
        createExperimentDescription(
            searchSpace,
            objectives
        )

    return {
        experimentDescription,
        allRes
    }
}