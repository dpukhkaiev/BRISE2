import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";
import type { ExperimentDescription } from "../../../entities/experiment/model/experiment.model";

function getParameterValues(
    parameter: string,
    allRes: PointExp[],
    experiment_description: ExperimentDescription
) {
    const values = allRes.map(
        point => point.configurations[parameter]
    );

    const searchSpace =
        experiment_description.Context?.SearchSpace?.[parameter];

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
    element: HTMLElement,
    allRes: PointExp[],
    rankParam1: string,
    rankParam2: string,
    rankObjective: string,
    experiment_description: ExperimentDescription
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
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

    const trace: Plotly.Data = {
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
            `${rankParam1}: %{customdata[0]}<br>` +
            `${rankParam2}: %{customdata[1]}<br>` +
            `${rankObjective}: %{marker.color}<extra></extra>`,

        customdata: allRes.map(point => [
            point.configurations[rankParam1],
            point.configurations[rankParam2]
        ])
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Rank Plot"
        },

        xaxis: {
            title: {
                text: rankParam1
            },

            ...(param1.tickvals && {
                tickmode: "array" as const,
                tickvals: param1.tickvals,
                ticktext: param1.ticktext
            })
        },

        yaxis: {
            title: {
                text: rankParam2
            },

            ...(param2.tickvals && {
                tickmode: "array" as const,
                tickvals: param2.tickvals,
                ticktext: param2.ticktext
            })
        },

        hovermode: "closest"
    };

    Plotly.react(element, [trace], layout);
}