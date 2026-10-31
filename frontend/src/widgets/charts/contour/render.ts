import type { Data, Layout } from 'plotly.js'
import type { PlotlyInstance } from '../model/chart.types'
import type { ParameterSpec } from "../../../entities/experiment/model/experiment.model";
import { cleanIdentifier } from "../../../shared/lib";

function getParameterValues(
    parameter: string,
    specsByName: Record<string, ParameterSpec>
) {
    const spec = specsByName[parameter];

    if (!spec) {
        return {
            values: []
        };
    }

    // Ordinal parameter
    if (
        spec.Type === "OrdinalHyperparameter" &&
        Array.isArray(spec.Categories)
    ) {
        const categories = spec.Categories;

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
    if (Array.isArray(spec.Categories)) {
        const categories = spec.Categories;

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
    plotly: PlotlyInstance,
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
    } | Record<string, never>,
    specsByName: Record<string, ParameterSpec>
) {
    if (result.contour == undefined || Object.keys(result.contour).length === 0) {
        plotly.purge(element)
        return
    }

    const xValues = getParameterValues(
        result.contour.x_name,
        specsByName
    );

    const yValues = getParameterValues(
        result.contour.y_name,
        specsByName
    );

    const trace: Data = {
        type: "contour",
        x: result.contour.x,
        y: result.contour.y,
        z: result.contour.z,
        colorscale: "Portland",
        contours: {
            coloring: "heatmap",
            showlabels: false
        },
        colorbar: {
            title: {
                text: result.contour.objective_name
            }
        }
    };

    const layout: Partial<Layout> = {
        title: {
            text: "Contour Plot"
        },
        autosize: true,
        hovermode: "closest",
        xaxis: {
            tickvals: xValues.tickvals,
            ticktext: xValues.ticktext,
            title: {
                text: cleanIdentifier(result.contour.x_name)
            }
        },
        yaxis: {
            tickvals: yValues.tickvals,
            ticktext: yValues.ticktext,
            title: {
                text: cleanIdentifier(result.contour.y_name)
            }
        }
    };

    plotly.react(element, [trace], layout);
}