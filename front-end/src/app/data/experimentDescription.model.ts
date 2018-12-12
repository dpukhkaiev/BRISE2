export interface ExperimentDescription {
    DomainDescription: DomainDescription
    TaskConfiguration: TaskConfiguration
    ModelConfiguration: ModelCreation
    SelectionAlgorithm: SelectionAlgorithm
}

interface DomainDescription {
    AllConfigurations: Array<any>
    DataFile: String
    DefaultConfiguration: Array<any>
    FeatureNames: Array<String>
}
interface TaskConfiguration {
    MaxTasksPerConfiguration: number
    MaxTimeToRunTask: number
    RepeaterDecisionFunction: String
    ResultDataTypes: Array<String>
    ResultStructure: Array<String>
    TaskName: String
    TaskParameters: Array<String>
    WorkerConfiguration
}
interface ModelCreation {
    MinimumAccuracy: number
    ModelTestSize: number
    ModelType: String // "regression" or "BO"

}
interface SelectionAlgorithm {
    NumberOfInitialConfigurations: Number
    SelectionType: String
}
