import {cleanIdentifier} from '../../../shared/lib'
export interface MatrixPayload {
  xAxis: string[]
  yAxis: string[]
  zMatrix: (number | null)[][]
}

 
export class DataTransformer {
   


  //Extracts clean axis categories from SearchSpace parameters

  public static extractAxisCategories(paramObj: any): string[] {
    if (!paramObj) return []
    if (Array.isArray(paramObj)) {
      return paramObj.map(cleanIdentifier)
    }
    if (paramObj.Categories && Array.isArray(paramObj.Categories)) {
      return paramObj.Categories.map(cleanIdentifier)
    }
    return Object.keys(paramObj)
      .filter(k => !['Type', 'Default', 'Level'].includes(k))
      .map(cleanIdentifier)
  }

  // builds the 2D Z-Matrix required for Plotly from raw prediction map and clean axis categories
  public static buildZMatrix(
    xAxis: string[],
    yAxis: string[],
    predictionsMap: Map<string, number>
  ): (number | null)[][] {
    if (!xAxis.length || !yAxis.length) return []

    return yAxis.map(yVal =>
      xAxis.map(xVal => {
        const key = `${yVal},${xVal}`
        const res = predictionsMap.get(key)
        return res !== undefined ? res : null
      })
    )
  }
  public static extractDynamicConfigValues(confObj: any): { yVal: string; xVal: string } {
    if (!confObj) return { yVal: '', xVal: '' }

    // if confObj nested in .configurations
    const target = confObj.configurations || confObj

    let rawY: any = ''
    let rawX: any = ''

    if (Array.isArray(target)) {
    // array
      rawY = target[0]
      rawX = target[1]
    } else if (typeof target === 'object') {
      // key value object ({ frequency: "...", threads: "..." })
     
      const values = Object.values(target)
      rawY = target.frequency ?? values[0]
      rawX = target.threads ?? values[1]
    }

    return {
      yVal: cleanIdentifier(rawY),
      xVal: cleanIdentifier(rawX)
    }
  }
}