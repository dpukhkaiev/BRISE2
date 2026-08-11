import { ref } from 'vue'


import { cleanIdentifier } from '../../../../shared/lib'



// return an array of values by key from all maps
export function unpack(set: any, key: any) {
    let selection: any = []
    set.forEach((point: any) => {
        selection.push(point.get(key));
    });
    return selection
}

// merge key and values arrays into a Map
export function zip(keys: Array<any>, values: Array<any>) {
    let result = new Map()
    if (keys.length == values.length) {
        keys.forEach((key, i) => result.set(key, values[i]))
    }
    return result
}


 function factoryDimension(parameter: String, valuesRange: Array<any>,  allPoints: Map<string, any>[]) {
    let rawDimValues = unpack(allPoints, parameter)
    // cleaning the row values
    let cleanedValues = rawDimValues.map((v: any) => cleanIdentifier(v))

    let dim: any = {
        label: String(parameter).replace(/_/g, " ")
    }

    // check if values are nummeric
    const isNumeric = cleanedValues.every((v: any) => v !== '' && v !== null && !isNaN(Number(v)))

    if (isNumeric) {
        dim.values = cleanedValues.map((v: any) => Number(v))
    } else {
        let categories: string[] = []

        if (valuesRange && Array.isArray(valuesRange) && valuesRange.length > 0) {
            categories = valuesRange.map((v: any) => cleanIdentifier(v))
        } else {
            // extract categories
            categories = Array.from(new Set(cleanedValues))
        }


        dim.tickvals = Array.from(Array(categories.length).keys())
        dim.ticktext = categories.map(String)

        // limit dim.values to only have numbers 
        dim.values = cleanedValues.map((val: any) => {
            const idx = dim.ticktext.indexOf(String(val))
            return idx !== -1 ? idx : 0
        })
    }

    return dim
}

export function dimmensionsData( resultParamsRange: Map<string, any> | undefined, experiment: string,  allPoints: Map<string, any>[]) {
    console.log('[DEBUG] resultParamsRange size:', resultParamsRange?.size, [...(resultParamsRange?.keys() ?? [])])
    let data: any = []
    resultParamsRange?.size && resultParamsRange.forEach((range: Array<any>, param: String) => {
        if (param != experiment) {
            let dim = factoryDimension(param, range, allPoints)
            data.push(dim)
        }
    })
    return data
}