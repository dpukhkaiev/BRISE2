import Plotly from 'plotly.js-dist-min'

export function renderParetoFront(
    element: HTMLElement, 
    result: { 
        "objective_names": string[],
        "all_points": Record<string, any>[], 
        "pareto_points": Record<string, any>[]
    },
    onlyShowParetoFront: boolean
) {

    if (result == undefined || result.objective_names.length === 0) {
        Plotly.purge(element)
        return
    }
    const allTrace = {
        x: result.all_points.map(p => p.x),
        y: result.all_points.map(p => p.y),
        mode: "markers" as const,
        type: "scatter" as const,
        name: "Runs",
        marker: {
            size: 8,
            color: "gray"
        },
        text: result.all_points.map(p => `Run ${p.number}`),
        hovertemplate:
            "%{text}<br>" +
            result.objective_names[0] +
            ": %{x}<br>" +
            result.objective_names[1] +
            ": %{y}<extra></extra>"
    }

    const paretoTrace = {
        x: result.pareto_points.map(p => p.x),
        y: result.pareto_points.map(p => p.y),
        mode: "markers" as const,
        type: "scatter" as const,
        name: "Pareto front",
        marker: {
            size: 10,
            color: "red",
            symbol: "diamond"
        },
        text: result.pareto_points.map(p => `Trial ${p.number}`),
        hovertemplate:
            "%{text}<br>" +
            result.objective_names[0] +
            ": %{x}<br>" +
            result.objective_names[1] +
            ": %{y}<extra></extra>"
    }

    const layout = {
        title: {
            text: "Pareto Front" 
        },
        xaxis: {
            title: {
                text: result.objective_names[0]
            }
        },
        yaxis: {
            title: {
                text: result.objective_names[1]
            }
        },
        hovermode: "closest" as const
    }

    const data = onlyShowParetoFront
    ? [paretoTrace]
    : [allTrace, paretoTrace]
    
    Plotly.react(element, data, layout);
}