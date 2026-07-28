import Plotly from 'plotly.js-dist-min'
import type { PointExp } from '../../../entities/main/model/plot.store'
import type { ExperimentDescription } from '../../../entities/experiment/model/experiment.model';

export function renderOptHist(
    element: HTMLElement,
    allRes: PointExp[],
    bestRes: PointExp[],
    experiment_description: ExperimentDescription
) {
    // X-axis data
    const xBest = Array.from(bestRes).map((i: any) => i['measured points']);
    // Results
    const yBest = Array.from(bestRes).map((i: any) => Object.values(i.results as Record<string, number>)[0]);

    const allResultSet = { // Data for all results
        x: Array.from(allRes).map((i: any) => i['measured points']),
        y: Array.from(allRes).map((i: any) => Object.values(i.results as Record<string, number>)[0]),
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: { color: 'rgba(67,67,67,1)', width: 1, shape: 'spline' as const, dash: 'dot' as const },
        //text: Array.from(allRes).map((i: any) => String(i['configurations'])),
        text: allRes.map(i =>
            Object.entries(i.configurations)
            .map(([key, value]) => `${key}: ${value}`)
            .join("<br>")
        ),
        marker: {
            color: 'rgba(255,64,129,1)',
            size: 8,
            symbol: 'x' as const
        },
        name: 'results'
    };
    const bestPointSet = { // Data for the best available results
        x: xBest,
        y: yBest,
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: { color: 'rgba(67,67,67,1)', width: 2, shape: 'spline' as const },
        name: 'best point',
        marker: { size: 6, symbol: 'x' as const, color: 'rgba(67,67,67,1)' }
    };

    const startEndPoint = { // Start & Finish markers
        x: [xBest[0], xBest[xBest.length - 1]],
        y: [yBest[0], yBest[yBest.length - 1]],
        type: 'scattergl' as const,
        mode: 'markers' as const,
        hoverinfo: 'none' as const,
        showlegend: false,
        marker: { color: 'rgba(255,64,129,1)', size: 10 }
    };

    const data = [allResultSet, bestPointSet, startEndPoint];

    const layout = {
        title: { text: 'The best results' } as const,
        showlegend: true,
        autosize: true,
        xaxis: {
            title: { text: 'Sequence number' } as const,
            showline: true,
            showgrid: false,
            zeroline: false,
            showticklabels: true,
            linecolor: 'rgb(204,204,204)',
            linewidth: 2,
            autotick: false,
            ticks: 'outside' as const,
            tickcolor: 'rgb(204,204,204)',
            tickwidth: 2,
            ticklen: 5,
            tickfont: {
                family: 'Roboto',
                size: 12,
                color: 'rgb(82, 82, 82)'
            }
        },
        yaxis: {
            title: { text: experiment_description['TaskConfiguration']?.['Objectives'][0] } as const,
            showgrid: false,
            zeroline: false,
            showline: true,
            linecolor: 'rgb(204,204,204)',
            showticklabels: true,
            ticks: 'outside' as const,
            tickcolor: 'rgb(204,204,204)',
            ticklen: 5,
            tickfont: {
                family: 'Roboto',
                size: 12,
                color: 'rgb(82, 82, 82)'
            }
        },
    };
    console.log(data)
    Plotly.react(element, data, layout);
}