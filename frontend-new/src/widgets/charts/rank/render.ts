import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderRank(
    element: HTMLElement,
    allRes: PointExp[],
    rankParam1: string,
    rankParam2: string,
    rankObjective: string
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
        return;
    }

    const trace: Plotly.Data = {
        type: "scatter",
        mode: "markers",
        x: allRes.map(p => p.configurations[rankParam1]),
        y: allRes.map(p => p.configurations[rankParam2]),
        marker: {
            size: 10,
            color: allRes.map(p => Number(p.results[rankObjective])),
            colorscale: "Viridis",
            colorbar: {
                title: {
                    text: rankObjective
                }
            }
        },
        text: allRes.map((_, i) => `Trial ${i + 1}`),
        hovertemplate:
            `${rankParam1}: %{x}<br>` +
            `${rankParam2}: %{y}<br>` +
            `${rankObjective}: %{marker.color}<extra></extra>`
    };

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Rank Plot"
        },
        xaxis: {
            title: {
                text: rankParam1
            }
        },
        yaxis: {
            title: {
                text: rankParam2
            }
        },
        hovermode: "closest"
    };

    Plotly.react(element, [trace], layout);
}