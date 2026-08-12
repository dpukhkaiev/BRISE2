import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";
import type { ExperimentDescription } from "../../../entities/experiment/model/experiment.model";

export function renderSlice(
    element: HTMLElement,
    allRes: PointExp[],
    sliceParam: string,
    sliceObjective: string,
    experiment_description: ExperimentDescription
) {
    if (
        allRes.length === 0 ||
        !sliceParam ||
        !sliceObjective
    ) {
        Plotly.purge(element);
        return;
    }

    const searchSpace =
        experiment_description.Context?.SearchSpace;

    const parameterDescription =
        searchSpace?.[sliceParam];

    const isOrdinal =
        parameterDescription?.Type === "OrdinalHyperparameter";

    const categories: string[] =
        isOrdinal && Array.isArray(parameterDescription.Categories)
            ? parameterDescription.Categories
            : [];

    let xValues: (string | number)[];

    if (isOrdinal) {
        // Map the categories to their position in the defined order
        const categoryIndex = new Map<string, number>(
            categories.map((category: string, index: number) => [
                category,
                index
            ])
        );

        xValues = allRes.map(point =>
            categoryIndex.get(
                String(point.configurations[sliceParam])
            ) ?? -1
        );
    } else {
        xValues = allRes.map(
            point => point.configurations[sliceParam]
        );
    }

    const trace: Plotly.Data = {
        type: "scatter",
        mode: "markers",

        x: xValues,

        y: allRes.map(
            point => Number(point.results[sliceObjective])
        ),

        text: allRes.map(
            (_, i) => `Trial ${i + 1}`
        ),

        hovertemplate:
            `${sliceParam}: %{customdata}<br>` +
            `${sliceObjective}: %{y}<br>` +
            "Run: %{text}<extra></extra>",

        customdata: allRes.map(
            point => point.configurations[sliceParam]
        ),

        marker: {
            size: 8,
            color: allRes.map((_, i) => i + 1),
            colorscale: "Blues",
            showscale: true,
            colorbar: {
                title: {
                    text: "Run"
                }
            }
        },

        showlegend: false
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Slice Plot"
        },
        autosize: true,
        hovermode: "closest",

        xaxis: {
            title: {
                text: sliceParam
            },

            ...(isOrdinal
                ? {
                    tickmode: "array" as const,
                    tickvals: categories.map(
                        (_: string, index: number) => index
                    ),
                    ticktext: categories.map(
                        (category: string) =>
                            category
                                .split(".")
                                .pop()
                                ?.replace(/_/g, " ") ?? category
                    )
                }
                : {})
        },

        yaxis: {
            title: {
                text: sliceObjective
            }
        }
    };

    Plotly.react(element, [trace], layout);
}