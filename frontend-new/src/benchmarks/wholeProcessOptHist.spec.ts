import {
    describe,
    it,
    expect,
    beforeEach,
    vi
} from "vitest"

import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { nextTick } from "vue"

import Plotly from "plotly.js-dist-min"

import { OptHist } from "../widgets/charts/opt-hist/index"

import { usePlotStore } from "../entities/main/model/plot.store"
import { useMainEventStore } from "../entities/main"

import { generateExperiment } from "./generateExperiment"


describe("Optimization History - complete frontend process", () => {

    const trialCounts = [
        10,
        20,
        50,
        100,
        500,
        1000
    ]

    const repetitions = 10

    beforeEach(() => {
        setActivePinia(createPinia())
    })

    it(
        "measures the complete OptHist process",
        async () => {

            const results: {
                trials: number
                parameters: number
                objectives: number
                run: number
                runtime: number
            }[] = []

            /*
             * Spy on Plotly.react.
             *
             * The real implementation is still executed.
             */
            const reactSpy = vi.spyOn(
                Plotly,
                "react"
            )

            for (const numTrials of trialCounts) {

                const experiment =
                    generateExperiment({
                        numTrials,
                        numParameters: 8,
                        numObjectives: 2,
                        seed: 42
                    })

                for (
                    let run = 0;
                    run < repetitions;
                    run++
                ) {

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
                                optHistObjective:
                                    "objective1"
                            }
                        })

                    /*
                     * Remove calls potentially caused by
                     * mounting the component.
                     */
                    reactSpy.mockClear()

                    const start =
                        performance.now()

                    /*
                     * This is what the real application
                     * effectively does when new experiment
                     * data becomes available.
                     */
                    mainStore.experiment_description =
                        experiment.experimentDescription

                    plotStore.allRes =
                        experiment.allRes

                    /*
                     * Wait until the Vue watcher has reacted
                     * and Plotly.react has actually been called.
                     */
                    await vi.waitFor(() => {
                        expect(
                            reactSpy
                        ).toHaveBeenCalled()
                    })

                    /*
                     * Get the promise returned by the REAL
                     * Plotly.react call.
                     */
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
                        parameters: 8,
                        objectives: 2,
                        run,
                        runtime
                    })

                    wrapper.unmount()
                }
            }

            reactSpy.mockRestore()

            console.table(results)

            expect(results).toHaveLength(
                trialCounts.length * repetitions
            )
        },
        120_000
    )
})