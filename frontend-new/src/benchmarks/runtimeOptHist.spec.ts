import { describe, it, expect } from "vitest"
import { generateExperiment } from "./generateExperiment"
import { renderOptHist } from "../widgets/charts/opt-hist/render.ts"

describe("Optimization History Runtime Benchmark", () => {
    const trialCounts = [
        10,
        20
    ]

    const repetitions = 10

    it("measures runtime for different numbers of trials", async () => {
        const results: {
            trials: number
            runtime: number
        }[] = []

        for (const numTrials of trialCounts) {
            const experiment = generateExperiment({
                numTrials: numTrials,
                numParameters: 8,
                numObjectives: 2,
                seed: 42
            })

            const runtimes: number[] = []

            for (let run = 0; run < repetitions; run++) {
                const element = document.createElement("div")

                document.body.appendChild(element)

                const start = performance.now()

                await renderOptHist(
                    element,
                    experiment.allRes,
                    experiment.experimentDescription,
                    "objective1"
                )

                const end = performance.now()

                runtimes.push(end - start)

                element.remove()
            }

            // Median is more robust against occasional browser spikes.
            const sorted = [...runtimes].sort((a, b) => a - b)

            const median =
                sorted[Math.floor(sorted.length / 2)]

            results.push({
                trials: numTrials,
                runtime: median
            })
        }

        console.table(results)

        expect(results).toHaveLength(trialCounts.length)
    }, 120_000)
})