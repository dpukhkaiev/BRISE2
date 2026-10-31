import type { Data, Layout } from 'plotly.js'
import type { PlotlyInstance } from '../model/chart.types'
import type { PointExp } from "../../../entities/main/model/plot.store";
import type { ParameterSpec } from "../../../entities/experiment/model/experiment.model";
import { cleanIdentifier } from "../../../shared/lib";

export function renderSlice(
    plotly: PlotlyInstance,
    element: HTMLElement,
    allRes: PointExp[],
    sliceParam: string,
    sliceObjective: string,
    specsByName: Record<string, ParameterSpec>
) {
    if (
        allRes.length === 0 ||
        !sliceParam ||
        !sliceObjective
    ) {
        plotly.purge(element);
        return;
    }

    const spec = specsByName[sliceParam];

    const isOrdinal =
        spec?.Type === "OrdinalHyperparameter";

    const categories: string[] =
        isOrdinal && Array.isArray(spec.Categories)
            ? spec.Categories
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

    const trace: Data = {
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
            `${cleanIdentifier(sliceParam)}: %{customdata}<br>` +
            `${sliceObjective}: %{y}<br>` +
            "Run: %{text}<extra></extra>",

        customdata: allRes.map(
            point => point.configurations[sliceParam]
        ),

        marker: {
            size: 8,
            color: allRes.map((_, i) => i + 1),
            colorscale: "Portland",
            showscale: true,
            colorbar: {
                title: {
                    text: "Run"
                }
            }
        },

        showlegend: false
    };

    const layout: Partial<Layout> = {
        title: {
            text: "Slice Plot"
        },
        autosize: true,
        hovermode: "closest",

        xaxis: {
            title: {
                text: cleanIdentifier(sliceParam)
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

    plotly.react(element, [trace], layout);
}