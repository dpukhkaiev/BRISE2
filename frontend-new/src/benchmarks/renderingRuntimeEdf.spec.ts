import { describe, it } from "vitest"
import { generateExperiment } from "./generateExperiment"
import { renderEdf } from "../widgets/charts/edf/render.ts"

describe("Edf Plot - Rendering Runtime Benchmark", () => {
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

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderEdf(
                    element,
                    experiment.allRes
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

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderEdf(
                    element,
                    experiment.allRes
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

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderEdf(
                    element,
                    experiment.allRes
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