import Plotly from "plotly.js-dist-min";
import type { PointExp } from "../../../entities/main/model/plot.store";

export function renderSlice(
    element: HTMLElement,
    allRes: PointExp[],
    sliceParam: string,
    sliceObjective: string
) {
    if (
        allRes.length === 0 ||
        !sliceParam ||
        !sliceObjective
    ) {
        Plotly.purge(element);
        return
    }

    const trace: Plotly.Data = {
        type: "scatter",
        mode: "markers",
        x: allRes.map(point => point.configurations[sliceParam]),
        y: allRes.map(point => Number(point.results[sliceObjective])),
        text: allRes.map((_, i) => `Trial ${i + 1}`),
        hovertemplate:
            `${sliceParam}: %{x}<br>` +
            `${sliceObjective}: %{y}<br>` +
            "Run: %{text}<extra></extra>",
        marker: {
            size: 8,
            color: allRes.map((_, i) => i + 1),
            colorscale: "Blues",
            showscale: true,
            colorbar: {
                title: {
                    text: "Run"
                }
            }
        },
        showlegend: false
    }

    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Slice Plot"
        },
        autosize: true,
        hovermode: "closest",
        xaxis: {
            title: {
                text: sliceParam
            }
        },
        yaxis: {
            title: {
                text: sliceObjective
            }
        }
    }

    Plotly.react(element, [trace], layout)
}