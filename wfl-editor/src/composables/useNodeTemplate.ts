

export interface FloatNode {
    type: 'float'
    name: string
    lower: number
    upper: number
    default: number
    level: number
}

export interface IntegerNode {
    type: 'integer'
    name: string
    lower: number
    upper: number
    default: number
    level: number
}

export interface CategoryNode {
    type: 'category'
    name: string
    children: Children[]
   
}

export interface NominalNode {
    type: 'nominal'
    name: string
    default: string
    children: Children[]
    level:number
}

export interface OrdinalNode {
    type: 'ordinal'
    name: string
    default: string
    children: Children[]
    level:number
}

export type Children = FloatNode | IntegerNode | NominalNode | OrdinalNode | CategoryNode


//
function indent(text: string, spaces: number = 2): string {
    const pad = ' '.repeat(spaces)
    return text.split('\n').map(line => pad + line).join('\n')
}

// function to check if the node has any content to wrap in the braces
function renderBlock(header: string, lines: string[]): string {
    if(lines.length === 0) {
        return header
    }

    return [
        `${header} {`,
        ...lines.map(line => indent(line)),
        `}`
    ].join('\n')

}

function floatTemplate(node: FloatNode): string {
    const lines: string[] = []
    if (node.lower !== undefined) lines.push(indent(`[Lower = ${node.lower}]`))
    if (node.upper !== undefined) lines.push(indent(`[Upper = ${node.upper}]`))
    if (node.default !== undefined) lines.push(indent(`[Default = ${node.default}]`))
    if (node.level !== undefined) lines.push(indent(`[Level = ${node.level}]`))   
 
    return renderBlock(`${node.name}: FloatHyperparameter`, lines)
}

export function integerTemplate(node: IntegerNode ): string {
    const lines: string[] = []
    if (node.lower !== undefined) lines.push(indent(`[Lower = ${node.lower}]`))
    if (node.upper !== undefined) lines.push(indent(`[Upper = ${node.upper}]`))
    if (node.default !== undefined) lines.push(indent(`[Default = ${node.default}]`))
    if (node.level !== undefined) lines.push(indent(`[Level = ${node.level}]`))   
 
    return renderBlock(`${node.name}: IntegerHyperparameter`, lines)
}

export function nominalTemplate(node: NominalNode, childrenWfl: string[]): string {
    const lines: string[] = [...childrenWfl]   
    if(node.default !== undefined) lines.push(indent(`[Default = "${node.default}"]`))
    if (node.level !== undefined) lines.push(indent(`[Level = ${node.level}]`))   
 
        return renderBlock(`${node.name} : NominalHyperparameter`, lines)
}

export function ordinalTemplate(node: OrdinalNode, childrenWfl: string[]): string {
    const lines: string[] = [...childrenWfl]
    if (node.default !== undefined) lines.push(indent(`[Default = "${node.default}"]`))
    if (node.level !== undefined) lines.push(indent(`[Level = ${node.level}]`))   
 
        return renderBlock(`${node.name} : OrdinalHyperparameter`, lines)
}


function categoryTemplate(node: CategoryNode, childrenWfl: string[]): string {
  
    return renderBlock(`${node.name} : Category`, childrenWfl)
}
    // templates together
    export const templates: Record<string, (node: any, children: string[]) => string> = {

    FloatHyperparameter: (node) => floatTemplate(node),
    IntegerHyperparameter: (node) => integerTemplate(node),
    NominalHyperparameter: (node, children) => nominalTemplate(node, children),
    OrdinalHyperparameter: (node, children) => ordinalTemplate(node, children),
    Category: (node, children) => categoryTemplate(node, children),
}


