import Plotly from "plotly.js-dist-min";
import type { ExperimentDescription } from "../../../entities/experiment/model/experiment.model";

function getParameterValues(
    parameter: string,
    experiment_description: ExperimentDescription
) {
    const searchSpace =
        experiment_description.Context?.SearchSpace?.[parameter];

    if (!searchSpace) {
        return {
            values: []
        };
    }

    // Ordinal parameter
    if (
        searchSpace.Type === "OrdinalHyperparameter" &&
        Array.isArray(searchSpace.Categories)
    ) {
        const categories = searchSpace.Categories;

        return {
            values: categories.map(
                (_: string, index: number) => index
            ),
            tickvals: categories.map(
                (_: string, index: number) => index
            ),
            ticktext: categories.map((category: string) => {
                const name = category.split(".").pop() ?? category;
                return name.replace(/_/g, " ");
            })
        };
    }

    // Categorical parameter
    if (Array.isArray(searchSpace.Categories)) {
        const categories = searchSpace.Categories;

        return {
            values: categories.map(
                (_: string, index: number) => index
            ),
            tickvals: categories.map(
                (_: string, index: number) => index
            ),
            ticktext: categories.map((category: string) =>
                String(category).replace(/_/g, " ")
            )
        };
    }

    return {
        values: []
    };
}

export function renderContour(
    element: HTMLElement,
    result: {
        contour: {
            x: number[],
            y: number[],
            z: (number | null)[][],
            x_name: string,
            y_name: string,
            objective_name: string
        }
    },
    experiment_description: ExperimentDescription

) {
    if (result.contour == undefined || Object.keys(result.contour).length === 0) {
        Plotly.purge(element)
        return
    }

    const xValues = getParameterValues(
        result.contour.x_name,
        experiment_description
    );

    const yValues = getParameterValues(
        result.contour.y_name,
        experiment_description
    );

    const trace: Plotly.Data = {
        type: "contour",
        x: result.contour.x,
        y: result.contour.y,
        z: result.contour.z,
        colorscale: "Viridis",
        contours: {
            coloring: "heatmap",
            showlabels: true
        },
        colorbar: {
            title: {
                text: result.contour.objective_name
            }
        }
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Contour Plot"
        },
        autosize: true,
        hovermode: "closest",
        xaxis: {
            tickvals: xValues.tickvals,
            ticktext: xValues.ticktext,
            title: {
                text: result.contour.x_name
            }
        },
        yaxis: {
            tickvals: yValues.tickvals,
            ticktext: yValues.ticktext,
            title: {
                text: result.contour.y_name
            }
        }
    };

    Plotly.react(element, [trace], layout);
}