export interface ExperimentDescription {
    DomainDescription: DomainDescription
    TaskConfiguration: TaskConfiguration
    ModelConfiguration: ModelCreation
    SelectionAlgorithm: SelectionAlgorithm
}

interface DomainDescription {
    DataFile: String
}
interface TaskConfiguration {
    MaxTasksPerConfiguration: number
    MaxTimeToRunTask: number
    RepeaterDecisionFunction: String
    Objectives: Array<String>
    ObjectivesDataTypes: Array<String>
    TaskName: String
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
