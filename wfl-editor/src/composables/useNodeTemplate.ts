import { ref, computed } from 'vue'
interface HyperparameterNode {
    id: string
    type: 'float' | 'integer' | 'nominal' | 'ordinal' | 'category'
    name: string
    constraints?: { lower?: number, upper?: number, default?: number }
    children?: HyperparameterNode[] | CategoryNode[]
}
interface FloatNode {
    type: 'float'
    name: string
    lower: number
    upper: number
    default: number
}
interface CategoryNode {
    type: 'category'
    name: string
    children: HyperparameterNode[]
}
type HyperparameterNode = FloatNode | IntegerNode | NominalNode | OrdinalNode | CategoryNode


function floatTemplate(node: ParsedXmlNode): string {
    const { name, lower, upper, default: def } = node
    let out = `${name} -> float`
    if (def !== undefined) out += ` = ${def}`

    const constraints: string[] = []
    if (lower !== undefined) constraints.push(`[${name} >= ${lower}]`)
    if (upper !== undefined) constraints.push(`[${name} <= ${upper}]`)

    return [out, ...constraints].join('\n')
}

export function integerTemplate(node: any): string {
    let out = `${node.name} -> integer`
    if (node.default !== undefined) out += ` = ${node.default}`
    const constraints: string[] = []
    if (node.lower !== undefined) constraints.push(`[${node.name} >= ${node.lower}]`)
    if (node.upper !== undefined) constraints.push(`[${node.name} <= ${node.upper}]`)
    return [out, ...constraints].join('\n')
}

export function nominalTemplate(node: any, childrenWfl: string[]): string {
    return [
        `${node.name}`,
        `xor`,
        `{`,
        ...childrenWfl.map(c => '    ' + c),
        `}`
    ].join('\n')
}
export function ordinalTemplate(node: any, childrenWfl: string[]): string {
    return [
        `${node.name}`,
        `xor`,
        `{`,
        ...childrenWfl.map(c => '    ' + c),
        `}`
    ].join('\n')
}


function categoryTemplate(node: any, childrenWfl: string[]): string {
    if (childrenWfl.length === 0) {
        return node.name  
    }
    return [
        `${node.name}`,
        `{`,
        ...childrenWfl.map(c => '    ' + c),
        `}`
    ].join('\n')

    // templates together
    export const templates: Record<string, (node: any, children: string[]) => string> = {
    FloatHyperparameter: (node) => floatTemplate(node),
    IntegerHyperparameter: (node) => integerTemplate(node),
    NominalHyperparameter: (node, children) => nominalTemplate(node, children),
    OrdinalHyperparameter: (node, children) => nominalTemplate(node, children),
    Category: (node, children) => categoryTemplate(node, children),
}

}