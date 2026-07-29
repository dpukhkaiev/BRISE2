import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderSlice(
    element: HTMLElement,
    allRes: PointExp[],
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
        return;
    }

    const parameters = Object.keys(allRes[0].configurations);
    const objectiveName = Object.keys(allRes[0].results)[0];

    const traces: Plotly.Data[] = [];

    parameters.forEach((parameter, index) => {
        traces.push({
        type: "scatter",
        mode: "markers",
        x: allRes.map(p => p.configurations[parameter]),
        y: allRes.map(p => Number(p.results[objectiveName])),
        text: allRes.map((_, i) => `Trial ${i + 1}`),
        hovertemplate:
            `${parameter}: %{x}<br>` +
            `${objectiveName}: %{y}<br>` +
            "Run: %{text}<extra></extra>",
        marker: {
            size: 8,
            color: allRes.map((_, i) => i + 1),
            colorscale: "Blues",
            showscale: index === parameters.length - 1,
            colorbar: {
                title: {
                    text: "Run"
                }
            }
        },
        xaxis: `x${index === 0 ? "" : index + 1}`,
        yaxis: `y${index === 0 ? "" : index + 1}`,
        showlegend: false
    });
    });

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Slice Plot"
        },
        grid: {
            rows: Math.ceil(parameters.length / 2),
            columns: Math.min(parameters.length, 2),
            pattern: "independent"
        },
        autosize: true,
        hovermode: "closest"
    };

    parameters.forEach((parameter, index) => {
        const axisId = index === 0 ? "" : index + 1;

        (layout as any)[`xaxis${axisId}`] = {
            title: {
                text: parameter
            }
        };

        (layout as any)[`yaxis${axisId}`] = {
            title: {
                text: objectiveName
            }
        };
    });

    Plotly.react(element, traces, layout);
}