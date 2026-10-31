export type ASTNode = SearchSpaceNode | NumericalHyperparameterNode | CategoricalHyperparameterNode | CategoryNode | ConstraintNode;

type Variant = 'int' | 'float' | 'nominal' | 'ordinal';

export interface SearchSpaceNode {
    type: 'root';
    name: string;
    body: ASTNode[];
}

export interface NumericalHyperparameterNode {
    type: 'Hyperparameter';
    variant: 'int' | 'float';
    id: string;
    name: string;
    lower: number;
    upper: number;
    default: number;
    level?: number;
    constraints?: ConstraintNode[];
}

export interface CategoricalHyperparameterNode {
    type: 'Hyperparameter';
    id: string;
    name: string;
    default?: string;
    level?: number;
    variant: 'nominal' | 'ordinal';
    manualCategories: string[];
    nestedCategories: (CategoryNode | ConstraintNode)[];
}

export interface CategoryNode {
    type: 'Category';
    id: string;
    name: string;
    children: (NumericalHyperparameterNode | CategoricalHyperparameterNode)[];
}

export type ConstraintNode = ComplexExpressionConstraint;


export interface ComplexExpressionConstraint {
    type: 'Constraint';
    id: string;
    kind: 'expression';
    value: string;
}