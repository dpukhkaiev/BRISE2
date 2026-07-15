import Plotly from 'plotly.js-dist-min'
import type { PointExp } from '../../../entities/main/model/plot.store'
import { ref } from 'vue'

const currentDiagram = ref()
let experiment: string = ''
let resultParamsRange = ref<Map<string, any>>()

function unpack(set: any, key: any) {
    let selection: any = []
    set.forEach((point: any) => {  // point is key value store - Map
        selection.push(point.get(key));
    });
    return selection
}

function factoryDimension(parameter: String, valuesRange: Array<any>, allRes: PointExp[]) {
    let dimValues = unpack(allRes, parameter)
    let dim: any = {
        values: dimValues,
        label: parameter.replace(/_/g, " ")
    }
    // If values are not numerical.
    if (valuesRange && (typeof valuesRange[0] == "string" || typeof valuesRange[0] == "boolean")) {
        dim.tickvals = Array.from(Array(valuesRange.length).keys())
        dim.ticktext = valuesRange
        dim.values = dimValues.map((value: any) => dim.tickvals[dim.ticktext.indexOf(value)])
    }
    return dim
}

function dimmensionsData(allRes: PointExp[]) {
    let data: any = [] // accommodate dimensional obj
    resultParamsRange.value?.size && resultParamsRange.value.forEach((range: Array<any>, param: String) => {
        if (param != experiment) {
            let dim = factoryDimension(param, range, allRes) // make dimensional object through all results by one parameter
            data.push(dim) // add new dimension object for plotting
        }
    })
    return data
}

export function renderParaCoord(
    element: HTMLElement,
    allRes: PointExp[]
){
    //console.log('currentDiagram:', currentDiagram.value)
    //console.log('rootParam:', rootParam.value)
    //console.log('element found:', document.getElementById(currentDiagram.value))

    var trace = [{
        type: 'parcoords' as const,
        line: {
            showscale: true,
            // reversescale: true,
            colorscale: 'Jet',
            color: unpack(allRes, 'result')
        },
        dimensions: dimmensionsData(allRes)
    }];

    var layout = {
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
    }

    Plotly.react(element, trace, layout)
}