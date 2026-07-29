import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderRank(
    element: HTMLElement,
    allRes: PointExp[],
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
        return;
    }

    const parameters = Object.keys(allRes[0].configurations);

    if (parameters.length < 2) {
        return;
    }

    const objective = Object.keys(allRes[0].results)[0];

    const xParam = parameters[0];
    const yParam = parameters[1];

    const trace: Plotly.Data = {
        type: "scatter",
        mode: "markers",
        x: allRes.map(p => p.configurations[xParam]),
        y: allRes.map(p => p.configurations[yParam]),
        marker: {
            size: 10,
            color: allRes.map(p => Number(p.results[objective])),
            colorscale: "Viridis",
            colorbar: {
                title: {
                    text: objective
                }
            }
        },
        text: allRes.map((_, i) => `Trial ${i + 1}`),
        hovertemplate:
            `${xParam}: %{x}<br>` +
            `${yParam}: %{y}<br>` +
            `${objective}: %{marker.color}<extra></extra>`
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Rank Plot"
        },
        xaxis: {
            title: {
                text: xParam
            }
        },
        yaxis: {
            title: {
                text: yParam
            }
        },
        hovermode: "closest"
    };

    Plotly.react(element, [trace], layout);
}