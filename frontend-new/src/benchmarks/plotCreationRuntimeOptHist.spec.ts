import { describe, it, expect, beforeEach, vi } from "vitest"

import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"

import Plotly from "plotly.js-dist-min"

import { OptHist } from "../widgets/charts/opt-hist/index"

import { usePlotStore } from "../entities/main/model/plot.store"
import { useMainEventStore } from "../entities/main"

import { generateExperiment } from "./generateExperiment"

import { server } from "vitest/browser"

const { writeFile } = server.commands


describe("Optimization History - Plot Creation Runtime Benchmark", () => {

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

    beforeEach(() => {
        setActivePinia(createPinia())
    })

    it("measures plot creation runtime for different numbers of trials", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        const reactSpy = vi.spyOn(
            Plotly,
            "react"
        )

        for (const numTrials of trialCounts) {
            const experiment =
                generateExperiment({
                    numTrials: numTrials,
                    numParameters: params,
                    numObjectives: objectives,
                    seed: 42
                })

            for (let run = 0; run < repetitions; run++) {
                const pinia = createPinia()

                setActivePinia(pinia)

                const plotStore =
                    usePlotStore()

                const mainStore =
                    useMainEventStore()

                const wrapper =
                    mount(OptHist, {
                        global: {
                            plugins: [pinia]
                        },
                        props: {
                            optHistObjective: "objective1"
                        }
                    })

                reactSpy.mockClear()

                const start = performance.now()

                mainStore.experiment_description = experiment.experimentDescription

                plotStore.allRes = experiment.allRes

                await vi.waitFor(() => {
                    expect(
                        reactSpy
                    ).toHaveBeenCalled()
                })

                const lastCall =
                    reactSpy.mock.results[
                        reactSpy.mock.results.length - 1
                    ]

                if (
                    lastCall.type !== "return"
                ) {
                    throw new Error(
                        "Plotly.react did not return normally"
                    )
                }

                await lastCall.value

                const runtime =
                    performance.now() - start

                results.push({
                    trials: numTrials,
                    params: params,
                    objectives: objectives,
                    runtime
                })

                wrapper.unmount()
            }
        }

        reactSpy.mockRestore()

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
            "./results/optHist-plotCreation-trials.csv",
            csv
        )
    }, 120_000)

    it("measures plot creation runtime for different numbers of params", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        const reactSpy = vi.spyOn(
            Plotly,
            "react"
        )

        for (const numParams of paramsCounts) {
            const experiment =
                generateExperiment({
                    numTrials: trials,
                    numParameters: numParams,
                    numObjectives: objectives,
                    seed: 42
                })

            for (let run = 0; run < repetitions; run++) {
                const pinia = createPinia()

                setActivePinia(pinia)

                const plotStore =
                    usePlotStore()

                const mainStore =
                    useMainEventStore()

                const wrapper =
                    mount(OptHist, {
                        global: {
                            plugins: [pinia]
                        },
                        props: {
                            optHistObjective: "objective1"
                        }
                    })

                reactSpy.mockClear()

                const start = performance.now()

                mainStore.experiment_description = experiment.experimentDescription

                plotStore.allRes = experiment.allRes

                await vi.waitFor(() => {
                    expect(
                        reactSpy
                    ).toHaveBeenCalled()
                })

                const lastCall =
                    reactSpy.mock.results[
                        reactSpy.mock.results.length - 1
                    ]

                if (
                    lastCall.type !== "return"
                ) {
                    throw new Error(
                        "Plotly.react did not return normally"
                    )
                }

                await lastCall.value

                const runtime =
                    performance.now() - start

                results.push({
                    trials: trials,
                    params: numParams,
                    objectives: objectives,
                    runtime
                })

                wrapper.unmount()
            }
        }

        reactSpy.mockRestore()

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
            "./results/optHist-plotCreation-params.csv",
            csv
        )
    }, 120_000)

    it("measures plot creation runtime for different numbers of objectives", async () => {
        const results: {
            trials: number
            params: number
            objectives: number
            runtime: number
        }[] = []

        const reactSpy = vi.spyOn(
            Plotly,
            "react"
        )

        for (const numObjectives of objectivesCounts) {
            const experiment =
                generateExperiment({
                    numTrials: trials,
                    numParameters: params,
                    numObjectives: numObjectives,
                    seed: 42
                })

            for (let run = 0; run < repetitions; run++) {
                const pinia = createPinia()

                setActivePinia(pinia)

                const plotStore =
                    usePlotStore()

                const mainStore =
                    useMainEventStore()

                const wrapper =
                    mount(OptHist, {
                        global: {
                            plugins: [pinia]
                        },
                        props: {
                            optHistObjective: "objective1"
                        }
                    })

                reactSpy.mockClear()

                const start = performance.now()

                mainStore.experiment_description = experiment.experimentDescription

                plotStore.allRes = experiment.allRes

                await vi.waitFor(() => {
                    expect(
                        reactSpy
                    ).toHaveBeenCalled()
                })

                const lastCall =
                    reactSpy.mock.results[
                        reactSpy.mock.results.length - 1
                    ]

                if (
                    lastCall.type !== "return"
                ) {
                    throw new Error(
                        "Plotly.react did not return normally"
                    )
                }

                await lastCall.value

                const runtime =
                    performance.now() - start

                results.push({
                    trials: trials,
                    params: params,
                    objectives: numObjectives,
                    runtime
                })

                wrapper.unmount()
            }
        }

        reactSpy.mockRestore()

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
            "./results/optHist-plotCreation-objectives.csv",
            csv
        )
    }, 120_000)
})