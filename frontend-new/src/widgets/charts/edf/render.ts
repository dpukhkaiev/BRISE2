import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderEdf(
    element: HTMLElement,
    allRes: PointExp[]
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
        return
    }

    const objectiveNames = Object.keys(allRes[0].results);

    const traces: Plotly.Data[] = objectiveNames.map(objectiveName => {
        const values = allRes
            .map(point => Number(point.results[objectiveName]))
            .sort((a, b) => a - b);

        const n = values.length;

        const probabilities = values.map((_, i) => (i + 1) / n);

        return {
            x: values,
            y: probabilities,
            type: "scatter",
            mode: "lines",
            name: objectiveName,
            line: {
                shape: "hv",
                width: 2
            },
            hovertemplate:
                `${objectiveName}: %{x}<br>` +
                `EDF: %{y:.2f}<extra></extra>`
        }
    })

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Empirical Distribution Function"
        },
        autosize: true,
        showlegend: true,
        legend: {
            title: {
                text: "Objectives"
            }
        },
        xaxis: {
            title: {
                text: "Objective value"
            }
        },
        yaxis: {
            title: {
                text: "Cumulative Probability"
            },
            range: [0, 1]
        },
        hovermode: "closest"
    }

    Plotly.react(element, traces, layout);
}