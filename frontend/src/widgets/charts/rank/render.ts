import type { Data, Layout } from 'plotly.js'
import type { PlotlyInstance } from '../model/chart.types'
import type { PointExp } from "../../../entities/main/model/plot.store";
import type { ExperimentDescription } from "../../../entities/experiment/model/experiment.model";
import { cleanIdentifier } from "../../../shared/lib";

function getParameterValues(
    parameter: string,
    allRes: PointExp[],
    experiment_description: ExperimentDescription
) {
    const values = allRes.map(
        point => point.configurations[parameter]
    );

    const searchSpace =
        (experiment_description.Context?.SearchSpace as Record<string, any> | undefined)?.[cleanIdentifier(parameter)];

    // Ordinal parameter
    if (
        searchSpace?.Type === "OrdinalHyperparameter" &&
        Array.isArray(searchSpace.Categories)
    ) {
        const categories = searchSpace.Categories;

        return {
            values: values.map(value => categories.indexOf(value)),
            tickvals: categories.map((_: string, index: number) => index),
            ticktext: categories.map((category: string) => {
                const name = category.split(".").pop() ?? category;
                return name.replace(/_/g, " ");
            })
        };
    }

    // Numeric parameter
    if (values.every(value => typeof value === "number")) {
        return {
            values
        };
    }

    // Non-ordinal categorical parameter
    const categories = Array.from(
        new Set(
            values.filter(
                (value): value is string => value !== undefined
            )
        )
    );

    return {
        values: values.map(value => categories.indexOf(value)),
        tickvals: categories.map((_, index) => index),
        ticktext: categories.map(category =>
            String(category).replace(/_/g, " ")
        )
    };
}

export function renderRank(
    plotly: PlotlyInstance,
    element: HTMLElement,
    allRes: PointExp[],
    rankParam1: string,
    rankParam2: string,
    rankObjective: string,
    experiment_description: ExperimentDescription
) {
    if (allRes.length === 0) {
        plotly.purge(element);
        return;
    }

    const param1 = getParameterValues(
        rankParam1,
        allRes,
        experiment_description
    );

    const param2 = getParameterValues(
        rankParam2,
        allRes,
        experiment_description
    );

    const trace: Data = {
        type: "scatter",
        mode: "markers",

        x: param1.values,
        y: param2.values,

        marker: {
            size: 10,
            color: allRes.map(
                p => Number(p.results[rankObjective])
            ),
            colorscale: "Portland",
            colorbar: {
                title: {
                    text: rankObjective
                }
            }
        },

        text: allRes.map(
            (_, i) => `Trial ${i + 1}`
        ),

        hovertemplate:
            `${cleanIdentifier(rankParam1)}: %{customdata[0]}<br>` +
            `${cleanIdentifier(rankParam2)}: %{customdata[1]}<br>` +
            `${rankObjective}: %{marker.color}<extra></extra>`,

        customdata: allRes.map(point => [
            point.configurations[rankParam1],
            point.configurations[rankParam2]
        ])
    };

    const layout: Partial<Layout> = {
        title: {
            text: "Rank Plot"
        },

        xaxis: {
            title: {
                text: cleanIdentifier(rankParam1)
            },

            ...(param1.tickvals && {
                tickmode: "array" as const,
                tickvals: param1.tickvals,
                ticktext: param1.ticktext
            })
        },

        yaxis: {
            title: {
                text: cleanIdentifier(rankParam2)
            },

            ...(param2.tickvals && {
                tickmode: "array" as const,
                tickvals: param2.tickvals,
                ticktext: param2.ticktext
            })
        },

        hovermode: "closest"
    };

    plotly.react(element, [trace], layout);
}