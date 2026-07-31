import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderEdf(
    element: HTMLElement,
    allRes: PointExp[]
) {
    if (allRes.length === 0) {
        Plotly.purge(element);
        return;
    }

    // Objective name (single-objective optimization)
    const objectiveName = Object.keys(allRes[0].results)[0];

    // Extract and sort objective values
    const values = allRes
        .map(point => Number(Object.values(point.results)[0]))
        .sort((a, b) => a - b);

    const n = values.length;

    // Empirical cumulative distribution
    const probabilities = values.map((_, i) => (i + 1) / n);

    const trace = {
        x: values,
        y: probabilities,
        type: "scatter" as const,
        mode: "lines" as const,
        line: {
            shape: "hv" as const, // staircase EDF
            width: 2
        },
        hovertemplate:
            `${objectiveName}: %{x}<br>` +
            `EDF: %{y:.2f}<extra></extra>`
    };

    const layout = {
        title: {
            text: "Empirical Distribution Function"
        },
        autosize: true,
        xaxis: {
            title: {
                text: objectiveName
            }
        },
        yaxis: {
            title: {
                text: "Cumulative Probability"
            },
            range: [0, 1]
        },
        hovermode: "closest" as const
    };

    Plotly.react(element, [trace], layout);
}