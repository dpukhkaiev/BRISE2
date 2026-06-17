import { CstParser } from 'chevrotain'
import {
    allTokens, LBracket, RBracket, Equals,
    Lower, Upper, Default, NumberLiteral, StringLiteral, ID
} from './lexer.ts'

export class myWflParser extends CstParser {
    constructor() {
        super(allTokens)
        this.performSelfAnalysis()
    }
}