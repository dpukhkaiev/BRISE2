import { describe, it } from "vitest"
import { generateExperiment } from "./generateExperiment"
import { renderContour } from "../widgets/charts/contour/render.ts"
import type { ExperimentDescription } from "../entities/experiment/model/experiment.model.ts"

function generateContourResult(
    experimentDescription: ExperimentDescription,
    param1: string,
    param2: string,
    objective = "objective1"
) {
    const searchSpace =
        experimentDescription.Context?.SearchSpace

    if (!searchSpace) {
        throw new Error("SearchSpace is missing")
    }

    const xParameter = searchSpace[param1]
    const yParameter = searchSpace[param2]

    if (!xParameter || !yParameter) {
        throw new Error("Parameter not found")
    }

    const getAxisLength = (parameter: any) => {
         if (
            parameter.Type === "OrdinalHyperparameter" ||
            Array.isArray(parameter.Categories)
        ) {
            return parameter.Categories.length
        }

        return 100
    }

    const width = getAxisLength(xParameter)
    const height = getAxisLength(yParameter)

    const x = Array.from(
        { length: width },
        (_, i) => i
    )

    const y = Array.from(
        { length: height },
        (_, i) => i
    )

    const z = Array.from(
        { length: height },
        (_, row) =>
            Array.from(
                { length: width },
                (_, col) => {
                    return (
                        Math.sin(col * 0.1) *
                        Math.cos(row * 0.1)
                    )
                }
            )
    )

    const contour: any = {
        x,
        y,
        z,
        x_name: param1,
        y_name: param2,
        objective_name: objective
    }

    if (
        xParameter.Type === "OrdinalHyperparameter" ||
        Array.isArray(xParameter.Categories)
    ) {
        contour.x_categories =
            xParameter.Categories
    }

    if (
        yParameter.Type === "OrdinalHyperparameter" ||
        Array.isArray(yParameter.Categories)
    ) {
        contour.y_categories =
            yParameter.Categories
    }

    return {
        contour
    }
}

describe("Contour Plot - Rendering Runtime Benchmark", () => {
    const trialCounts = [
        25,
        50,
        100,
        250,
        500,
        1000
    ]

    const paramsCounts = [
        2,
        4,
        8,
        16,
        32
    ]

    const objectivesCounts = [
        1,
        2,
        3,
        4,
        5
    ]

    const params = 8
    const objectives = 2
    const trials = 50

    const repetitions = 10

    it("measures rendering runtime for different numbers of trials", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        for (const numTrials of trialCounts) {
            const experiment = generateExperiment({
                numTrials: numTrials,
                numParameters: params,
                numObjectives: objectives,
                seed: 42
            })

            const result = generateContourResult(
                experiment.experimentDescription,
                "parameter1",
                "parameter2",
                "objective1"
            )

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderContour(
                    element,
                    result,
                    experiment.experimentDescription,
                )

                const end = performance.now()

                results.push({
                    trials: numTrials,
                    params: params,
                    objectives: objectives,
                    runtime: (end-start)
                })

                element.remove()
            }
        }

        console.table(results)
    }, 120_000)

    it("measures rendering runtime for different numbers of params", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        for (const numParams of paramsCounts) {
            const experiment = generateExperiment({
                numTrials: trials,
                numParameters: numParams,
                numObjectives: objectives,
                seed: 42
            })

            const result = generateContourResult(
                experiment.experimentDescription,
                "parameter1",
                "parameter2",
                "objective1"
            )

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderContour(
                    element,
                    result,
                    experiment.experimentDescription,
                )

                const end = performance.now()

                results.push({
                    trials: trials,
                    params: numParams,
                    objectives: objectives,
                    runtime: (end-start)
                })

                element.remove()
            }
        }

        console.table(results)
    }, 120_000)

    it("measures rendering runtime for different numbers of objectives", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        for (const numObjectives of objectivesCounts) {
            const experiment = generateExperiment({
                numTrials: trials,
                numParameters: params,
                numObjectives: numObjectives,
                seed: 42
            })

            const result = generateContourResult(
                experiment.experimentDescription,
                "parameter1",
                "parameter2",
                "objective1"
            )

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderContour(
                    element,
                    result,
                    experiment.experimentDescription,
                )

                const end = performance.now()

                results.push({
                    trials: trials,
                    params: params,
                    objectives: numObjectives,
                    runtime: (end-start)
                })

                element.remove()
            }
        }

        console.table(results)
    }, 120_000)
})