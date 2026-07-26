import Plotly from 'plotly.js-dist-min'
import type { PointExp } from '../../../entities/main/model/plot.store'
import { ref } from 'vue'

const currentDiagram = ref()

function createParamsRange(searchspace: any): Map<string, any> {
    const parameterNames = Object.keys(
        searchspace.boundaries[0].Boundaries
    );

    const rangeValues = Object.values(
        searchspace.boundaries[0].Boundaries
    );

    return new Map(
        parameterNames.map((name, index) => [
            name,
            rangeValues[index]
        ])
    );
}

function factoryDimension(
    parameter: string,
    valuesRange: Array<any>,
    allRes: PointExp[]
) {
    let dimValues = allRes.map(point => point.configurations[parameter]);

    let dim: any = {
        values: dimValues,
        label: parameter.replace(/_/g, " ")
    };

    if (
        valuesRange &&
        (typeof valuesRange[0] === "string" ||
         typeof valuesRange[0] === "boolean")
    ) {
        dim.tickvals = Array.from(Array(valuesRange.length).keys());
        dim.ticktext = valuesRange;

        dim.values = dimValues.map(
            value => dim.tickvals[dim.ticktext.indexOf(value)]
        );
    }

    return dim;
}

function dimensionsData(
    allRes: PointExp[],
    resultParamsRange: Map<string, any>
) {
    const data: any[] = [];

    resultParamsRange.forEach(
        (range: Array<any>, param: string) => {
            console.log("parameter:", param);
            if (param !== "root") {
                data.push(factoryDimension(param, range, allRes));
            }
        }
    )

    return data;
}

export function renderParaCoord(
    element: HTMLElement,
    allRes: PointExp[],
    searchspace: any
) {
    const resultParamsRange = createParamsRange(searchspace);

    const trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            colorscale: 'Jet',
            color: allRes.map(point => Object.values(point.results)[0])
        },
        dimensions: dimensionsData(allRes, resultParamsRange)
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

    console.log("allRes:", allRes);
    console.log("dimensions:", dimensionsData(allRes, resultParamsRange));
    console.log("colors:", allRes.map(point => Object.values(point.results)[0]));

    Plotly.react(element, trace, layout);
}