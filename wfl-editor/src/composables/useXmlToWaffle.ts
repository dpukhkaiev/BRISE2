import {templates} from './useNodeTemplate.ts'

interface ParsedNode {
    tagName: string
    name: string
    lower?: number
    upper?: number
    default?: number
    children: ParsedNode[]
}


function parseXmlElement(el: Element): ParsedNode {
    const constraintsEl = el.querySelector('Constraints')
    const lower = constraintsEl?.querySelector('lower')?.textContent
    const upper = constraintsEl?.querySelector('upper')?.textContent
    const def = constraintsEl?.querySelector('default')?.textContent

    const childElements = Array.from(el.children).filter(c => c.tagName !== 'Constraints')

    return {
        tagName: el.tagName,
        name: el.getAttribute('name') || '',
        lower: lower ? Number(lower) : undefined,
        upper: upper ? Number(upper) : undefined,
        default: def ? Number(def) : undefined,
        children: childElements.map(parseXmlElement)
    }
}

function generateWfl(node: ParsedNode): string {
    const childrenWfl = node.children.map(generateWfl)
    const template = templates[node.tagName]
    if (!template) return `// Unknown type: ${node.tagName}`
    return template(node, childrenWfl)
}

export function useXmlToWfl() {
    function convert(xmlString: string): string {
        const doc = new DOMParser().parseFromString(xmlString, 'application/xml')
        const root = doc.documentElement // SearchSpace
        const topLevelNodes = Array.from(root.children).map(parseXmlElement)
        return topLevelNodes.map(generateWfl).join('\n\n')
    }
    return { convert }
}