export interface ExperimentDescription {
    DomainDescription: DomainDescription
    TaskConfiguration: TaskConfiguration
    ModelConfiguration: ModelCreation
    SelectionAlgorithm: SelectionAlgorithm
}

interface DomainDescription {
    DataFile: String
    HyperparameterNames: Array<String>
}
interface TaskConfiguration {
    MaxTasksPerConfiguration: number
    MaxTimeToRunTask: number
    RepeaterDecisionFunction: String
    ResultDataTypes: Array<String>
    ResultStructure: Array<String>
    TaskName: String
    TaskParameters: Array<String>
    Scenario
}
interface ModelCreation {
    MinimumAccuracy: number
    minimalTestingSize: number
    maximalTestingSize: number
    ModelType: String // "regression" or "BO"

}
interface SelectionAlgorithm {
    SelectionType: String
}
