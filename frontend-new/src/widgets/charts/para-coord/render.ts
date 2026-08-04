import Plotly from 'plotly.js-dist-min'
import type { PointExp } from '../../../entities/main/model/plot.store'
import { ref } from 'vue'

const currentDiagram = ref()

function factoryDimension(
    parameter: string,
    allRes: PointExp[]
) {
    const values = allRes.map(
        point => point.configurations[parameter]
    );

    const dimension: any = {
        label: parameter.replace(/_/g, " ")
    };

    const firstValue = values.find(v => v !== undefined);

    if (typeof firstValue === "number") {
        dimension.values = values;
        dimension.range = [
            Math.min(...values),
            Math.max(...values)
        ];
    } 
    else {
        const categories = Array.from(new Set(values));

        dimension.values = values.map(
            value => categories.indexOf(value)
        );

        dimension.tickvals = categories.map(
            (_, i) => i
        );

        dimension.ticktext = categories.map(
            String
        );
    }

    return dimension;
}

function dimensionsData(
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string
) {
    const dimensions = paraCoordParams.map(parameter =>
        factoryDimension(parameter, allRes)
    );

    const objectiveValues = allRes.map(
        point => Number(point.results[paraCoordObjective])
    );

    dimensions.push({
        label: paraCoordObjective,
        values: objectiveValues
    });

    return dimensions;
}

export function renderParaCoord(
    element: HTMLElement,
    allRes: PointExp[],
    paraCoordParams: string[],
    paraCoordObjective: string
) {
    if (
        allRes.length === 0 ||
        paraCoordParams.length === 0 ||
        !paraCoordObjective
    ) {
        Plotly.purge(element);
        return;
    }

    const objectiveValues = allRes.map(
        point => Number(point.results[paraCoordObjective])
    );

    const trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            colorscale: 'Jet',
            color: objectiveValues
        },
        dimensions: dimensionsData(
            allRes,
            paraCoordParams,
            paraCoordObjective
        )
    }];

    const layout = {
        margin: {
            l: 150,
        },
        title: {
            text: currentDiagram.value,
            font: {
                size: 20
            },
            xref: 'paper' as const,
            x: 0.05,
        }
    };

    Plotly.react(element, trace, layout);
}