import Plotly from "plotly.js-dist-min";

export function renderContour(
    element: HTMLElement,
    result: {
        contour: {
            x: number[],
            y: number[],
            z: number[][],
            x_name: string,
            y_name: string,
            objective_name: string
        }
    }
) {

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
        },
        hovertemplate:
            `${result.contour.x_name}: %{x}<br>` +
            `${result.contour.y_name}: %{y}<br>` +
            `${result.contour.objective_name}: %{z}<extra></extra>`
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Contour Plot"
        },
        autosize: true,
        hovermode: "closest",
        xaxis: {
            title: {
                text: result.contour.x_name
            }
        },
        yaxis: {
            title: {
                text: result.contour.y_name
            }
        }
    };

    Plotly.react(element, [trace], layout);
}