import type { PlotlyInstance } from '../model/chart.types'
import type { PointExp } from '../../../entities/main/model/plot.store'
import type { ExperimentDescription } from '../../../entities/experiment/model/experiment.model';

export function renderOptHist(
    plotly: PlotlyInstance,
    element: HTMLElement,
    allRes: PointExp[],
    experiment_description: ExperimentDescription,
    optHistObjective: string,
    solution: PointExp | null = null
) {
    if (allRes.length === 0) {
        plotly.purge(element);
        return;
    }

    const objectives = experiment_description.Context?.TaskConfiguration?.Objectives;

    const minimize = objectives?.[optHistObjective]?.Minimization ?? true;
  
    // Calculate the best-so-far points for the selected objective
    const xBest: number[] = [];
    const yBest: number[] = [];

    let bestValue = minimize ? Infinity : -Infinity;

    for (const point of allRes) {
        const value = point.results[optHistObjective];

        if (value === undefined) continue;

        if (minimize) {
            bestValue = Math.min(bestValue, value);
        } else {
            bestValue = Math.max(bestValue, value);
        }

        xBest.push(point["measured points"]);
        yBest.push(bestValue);
    }

    const allResultSet = {
        x: allRes.map(i => i["measured points"]),
        y: allRes.map(i => i.results[optHistObjective]),
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: {
            color: 'rgba(67,67,67,1)',
            width: 1,
            shape: 'spline' as const,
            dash: 'dot' as const
        },
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

    const bestPointSet = {
        x: xBest,
        y: yBest,
        type: 'scattergl' as const,
        mode: 'lines+markers' as const,
        line: {
            color: 'rgba(67,67,67,1)',
            width: 2,
            shape: 'spline' as const
        },
        name: 'best point',
        marker: {
            size: 6,
            symbol: 'x' as const,
            color: 'rgba(67,67,67,1)'
        }
    };

    const startEndPoint = {
        x: [xBest[0], xBest[xBest.length - 1]],
        y: [yBest[0], yBest[yBest.length - 1]],
        type: 'scattergl' as const,
        mode: 'markers' as const,
        hoverinfo: 'none' as const,
        showlegend: false,
        marker: {
            color: 'rgba(255,64,129,1)',
            size: 10
        }
    };

    // final configuration suggested by BRISE
    const solutionValue = solution?.results[optHistObjective];
    const solutionMarker = solution && solutionValue !== undefined ? {
        x: [solution["measured points"]],
        y: [solutionValue],
        type: 'scattergl' as const,
        mode: 'markers' as const,
        hoverinfo: 'text' as const,
        text: 'Final solution',
        name: 'Solution',
        marker: {
            color: 'Gold',
            size: 16,
            symbol: 'star' as const,
            line: { color: 'black', width: 1 }
        }
    } : null;

    const data = solutionMarker
        ? [allResultSet, bestPointSet, startEndPoint, solutionMarker]
        : [allResultSet, bestPointSet, startEndPoint];

    const layout = {
        title: {
            text: 'The best results'
        },
        showlegend: true,
        autosize: true,
        xaxis: {
            title: { text: 'Sequence number' },
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
            title: { text: optHistObjective },
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
        }
    };

    plotly.react(element, data, layout);
}