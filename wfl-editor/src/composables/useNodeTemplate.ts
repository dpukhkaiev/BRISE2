import { ref, computed, pushScopeId } from 'vue'

export interface FloatNode {
    type: 'float'
    name: string
    lower: number
    upper: number
    default: number
}

export interface IntegerNode {
    type: 'integer'
    name: string
    lower: number
    upper: number
    default: number
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

}

export interface OrdinalNode {
 type: 'ordinal'
    name: string
    default: string
    children: Children[]

}

export type Children = FloatNode | IntegerNode | NominalNode | OrdinalNode | CategoryNode


//
function indent(text: string, spaces: number = 2): string {
    const pad = ' '.repeat(spaces)
    return text.split('\n').map(line => pad + line).join('\n')
}

function floatTemplate(node: FloatNode): string {


    const constraints = [`${node.name}: FloatHyperparameter {`]
    if (node.lower !== undefined) constraints.push(indent(`[Lower = ${node.lower}]`))
    if (node.upper !== undefined) constraints.push(indent(`[Upper = ${node.upper}]`))
    if (node.default !== undefined) constraints.push(indent(`[Default = ${node.default}]`))
 
    constraints.push(`}`)
    return constraints.join('\n')
}

export function integerTemplate(node: IntegerNode ): string {
  
    const constraints = [`${node.name}: IntegerHyperparameter {`]
    if (node.lower !== undefined) constraints.push(indent(`[Lower = ${node.lower}]`))
    if (node.upper !== undefined) constraints.push(indent(`[Upper = ${node.upper}]`))
    if (node.default !== undefined) constraints.push(indent(`[Default = ${node.default}]`))
   
    constraints.push(`}`)
    return constraints.join('\n')
}

export function nominalTemplate(node: NominalNode, childrenWfl: string[]): string {
    const lines = [`${node.name} : NominalHyperparameter {` ]     
    lines.push(...childrenWfl.map(c => indent(c)))
    if(node.default !== undefined) lines.push(indent(`[Default = "${node.default}"]`))
    lines.push(`}`)
    return lines.join('\n')
}

export function ordinalTemplate(node: OrdinalNode, childrenWfl: string[]): string {
    const lines = [ `${node.name} : OrdinalHyperparameter {`]
    lines.push(...childrenWfl.map(c =>indent(c))) 
    if (node.default !== undefined) lines.push(indent(`[Default = "${node.default}"]`))
    lines.push(`}`)
    return lines.join('\n')
}


function categoryTemplate(node: CategoryNode, childrenWfl: string[]): string {
  
    return [
        `${node.name} : Category {`,
        ...childrenWfl.map(c => indent(c)),
        `}`
    ].join('\n')
}
    // templates together
    export const templates: Record<string, (node: any, children: string[]) => string> = {

    FloatHyperparameter: (node) => floatTemplate(node),
    IntegerHyperparameter: (node) => integerTemplate(node),
    NominalHyperparameter: (node, children) => nominalTemplate(node, children),
    OrdinalHyperparameter: (node, children) => ordinalTemplate(node, children),
    Category: (node, children) => categoryTemplate(node, children),
}


