export interface ExperimentDescription {
    DomainDescription: DomainDescription
    TaskConfiguration: TaskConfiguration
    Predictor: Predictor
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
interface Predictor {
    models: Array<any>
    ModelType: String
}
interface SelectionAlgorithm {
    SelectionType: String
}
