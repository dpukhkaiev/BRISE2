import { describe, it } from "vitest"
import { generateExperiment } from "./generateExperiment"
import { renderParetoFront } from "../widgets/charts/pareto-front/render.ts"

import { server } from "vitest/browser"

const { writeFile } = server.commands

describe("Pareto Front - Rendering Runtime Benchmark", () => {
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
    const trials = 100

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

            const result = {
                "objective_names": ["objective1", "objective2"],
                "all_points": [{} as Record<string, any>],
                "pareto_points": [{} as Record<string, any>]
            }

            for (let trial = 0; trial < numTrials; trial++) {
                if (trial % 10 == 0) {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                    result.pareto_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                } else {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                }
            }

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderParetoFront(
                    element,
                    result,
                    false
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

        const csv = [
            "trials,parameters,objectives,runtime",
            ...results.map(result =>
                [
                    result.trials,
                    result.params,
                    result.objectives,
                    result.runtime
                ].join(",")
            )
        ].join("\n")

        await writeFile(
            "./results/paretoFront-rendering-trials.csv",
            csv
        )
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

            const result = {
                "objective_names": ["objective1", "objective2"],
                "all_points": [{} as Record<string, any>],
                "pareto_points": [{} as Record<string, any>]
            }

            for (let trial = 0; trial < trials; trial++) {
                if (trial % 10 == 0) {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                    result.pareto_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                } else {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                }
            }

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderParetoFront(
                    element,
                    result,
                    false
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

        const csv = [
            "trials,parameters,objectives,runtime",
            ...results.map(result =>
                [
                    result.trials,
                    result.params,
                    result.objectives,
                    result.runtime
                ].join(",")
            )
        ].join("\n")

        await writeFile(
            "./results/paretoFront-rendering-params.csv",
            csv
        )
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

            const result = {
                "objective_names": ["objective1", "objective2"],
                "all_points": [{} as Record<string, any>],
                "pareto_points": [{} as Record<string, any>]
            }

            for (let trial = 0; trial < trials; trial++) {
                if (trial % 10 == 0) {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                    result.pareto_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                } else {
                    result.all_points.push({
                        "objective1": experiment.allRes[trial].results["objective1"],
                        "objective2": experiment.allRes[trial].results["objective2"]
                    })
                }
            }

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderParetoFront(
                    element,
                    result,
                    false
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

        const csv = [
            "trials,parameters,objectives,runtime",
            ...results.map(result =>
                [
                    result.trials,
                    result.params,
                    result.objectives,
                    result.runtime
                ].join(",")
            )
        ].join("\n")

        await writeFile(
            "./results/paretoFront-rendering-objectives.csv",
            csv
        )
    }, 120_000)
})