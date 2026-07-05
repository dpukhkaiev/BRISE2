import {templates} from './useNodeTemplate.ts'
import type { FloatNode, IntegerNode, NominalNode, OrdinalNode, CategoryNode, Children } from './useNodeTemplate.ts'

const tagToType: Record<string, Children['type']> = {
    FloatHyperparameter: 'float',
    IntegerHyperparameter: 'integer',
    NominalHyperparameter: 'nominal',
    OrdinalHyperparameter: 'ordinal',
    Category: 'category'
}


function parseXmlElement(el: Element): Children {
    const constraintsEl = el.querySelector('Constraints')
    const lowerText = constraintsEl?.querySelector('lower')?.textContent
    const upperText = constraintsEl?.querySelector('upper')?.textContent
    const defText = constraintsEl?.querySelector('default')?.textContent

    const childElements = Array.from(el.children).filter(c => c.tagName !== 'Constraints')
   const children = childElements.map(parseXmlElement)

       const tagName = el.tagName
    const type = tagToType[tagName]
    const name = el.getAttribute('name') || ''

    const lower = lowerText ? Number(lowerText) : undefined
    const upper = upperText ? Number(upperText) : undefined
    const def = defText ? Number(defText) : undefined
   
    switch (type) {
        case 'float':
            return { type: 'float', name, lower, upper, default: def } as FloatNode
        case 'integer':
            return { type: 'integer', name, lower, upper, default: def } as IntegerNode
        case 'nominal':
            return { type: 'nominal', name, lower, upper, default: def, children } as NominalNode
        case 'ordinal':
            return { type: 'ordinal', name, lower, upper, default: def, children } as OrdinalNode
        case 'category':
            return { type: 'category', name, children } as CategoryNode
        default:
            throw new Error(`Unknown tag: ${tagName}`)
    }
}

function generateWfl(node: Children): string {
    const childrenWfl = 'children' in node
        ? node.children.map(generateWfl)
        : []

    const tagName = Object.entries(tagToType).find(([_, t]) => t === node.type)?.[0]
    if (!tagName) return `// Unknown type: ${node.type}`

    const template = templates[tagName]
    if (!template) return `// No template for: ${tagName}`

    return template(node, childrenWfl)
}

export function useXmlToWfl() {
    function convert(xmlString: string): string {
        const doc = new DOMParser().parseFromString(xmlString, 'application/xml')
        const root = doc.documentElement // SearchSpace
        // generate inner waffle content for the top level nodes
        const topLevelNodes = Array.from(root.children).map(parseXmlElement)
        const innerContent = topLevelNodes.map(generateWfl).join('\n\n')
        
        const indentedContent = innerContent
            .split('\n')
            .map(line => '  ' + line)
            .join('\n')

            return `Searchspace {\n${indentedContent}\n}`
    }
    return { convert }
}