import { createToken, Lexer } from 'chevrotain'


export const WhiteSpace = createToken({
    name: 'WhiteSpace',
    pattern: /\s+/,
    group: Lexer.SKIPPED
})

export const LineComment = createToken({
    name: 'LineComment',
    pattern: /\/\/[^\n]*/,
    group: Lexer.SKIPPED
})

export const BlockComment = createToken({
    name: 'BlockComment',
    pattern: /\/\*(\*(?!\/)|[^*])*\*\//,
    group: Lexer.SKIPPED
})

//Keywords (has to be before id)

export const NominalHyperparameter = createToken({
    name: 'NominalHyperparameter',
    pattern: /NominalHyperparameter/
})
export const OrdinalHyperparameter = createToken({
    name: 'OrdinalHyperparameter',
    pattern: /OrdinalHyperparameter/
})
export const IntegerHyperparameter = createToken({
    name: 'IntegerHyperparameter',
    pattern: /IntegerHyperparameter/
})
export const FloatHyperparameter = createToken({
    name: 'FloatHyperparameter',
    pattern: /FloatHyperparameter/
})
export const Category = createToken({
    name: 'Category',
    pattern: /Category/
})
export const SearchSpace = createToken({
    name: 'SearchSpace',
    pattern: /SearchSpace/
})
export const Lower = createToken({ name: 'Lower', pattern: /Lower/ })
export const Upper = createToken({ name: 'Upper', pattern: /Upper/ })
export const Default = createToken({ name: 'Default', pattern: /Default/ })
export const XorKw = createToken({ name: 'XorKw', pattern: /xor/ })

// Symbols

export const LBrace = createToken({ name: 'LBrace', pattern: /\{/ })
export const RBrace = createToken({ name: 'RBrace', pattern: /\}/ })
export const LBracket = createToken({ name: 'LBracket', pattern: /\[/ })
export const RBracket = createToken({ name: 'RBracket', pattern: /\]/ })
export const Colon = createToken({ name: 'Colon', pattern: /:/ })
export const Equals = createToken({ name: 'Equals', pattern: /=/ })

// Literals

export const StringLiteral = createToken({
    name: 'StringLiteral',
    pattern: /"[^"]*"/
})

export const NumberLiteral = createToken({
    name: 'NumberLiteral',
    pattern: /-?(\d+\.\d+|\d+)/
})

// identifier 

export const ID = createToken({
    name: 'ID',
    pattern: /[a-zA-Z_][a-zA-Z0-9_]*/
})

// important for chevrotain 

export const allTokens = [
    WhiteSpace,
    LineComment,
    BlockComment,
    // Keywords 
    NominalHyperparameter,
    OrdinalHyperparameter,
    IntegerHyperparameter,
    FloatHyperparameter,
    Category,
    SearchSpace,
    Lower,
    Upper,
    Default,
    XorKw,
    LBrace, RBrace, LBracket, RBracket, Colon, Equals,
    StringLiteral,
    NumberLiteral,
    ID
]

export const WflLexer = new Lexer(allTokens)