export type ASTNode =
    | { type: 'Program'; body: ASTNode[] }
    | { type: 'NumberTemplate'; id: string; name: string; variant: 'int' | 'float' }
    | { type: 'CategoricalTemplate'; id: string; name: string; variant: 'nominal' | 'ordinal'; categories: string[]; children: string[] };