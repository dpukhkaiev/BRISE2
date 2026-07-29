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

function dimensionsData(allRes: PointExp[]) {
    const parameters = Object.keys(allRes[0].configurations);

    const dimensions = parameters.map(
        parameter => factoryDimension(parameter, allRes)
    );

    const objectiveName = Object.keys(allRes[0].results)[0];

    const objectiveValues = allRes.map(
        point => Number(point.results[objectiveName])
    );

    dimensions.push({
        label: objectiveName,
        values: objectiveValues
    });

    return dimensions;
}

export function renderParaCoord(
    element: HTMLElement,
    allRes: PointExp[],
) {
    if (allRes.length === 0) {
        Plotly.purge(element)
        return
    }

    const trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            colorscale: 'Jet',
            color: allRes.map(point => Object.values(point.results)[0])
        },
        dimensions: dimensionsData(allRes)
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