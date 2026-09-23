export interface MatrixPayload {
  xAxis: string[]
  yAxis: string[]
  zMatrix: (number | null)[][]
}

 
export class DataTransformer {
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
}