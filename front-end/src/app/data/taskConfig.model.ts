export interface TaskConfig {
    DomainDescription: DomainDescription
    ExperimentsConfiguration: ExperimentsConfiguration
    ModelCreation: ModelCreation
    SelectionAlgorithm: SelectionAlgorithm
}

interface DomainDescription {
    AllConfigurations: Array<any>
    DataFile: String
    DefaultConfiguration: Array<any>
    FeatureNames: Array<String>
}
interface ExperimentsConfiguration {
    MaxRepeatsOfExperiment: number
    MaxTimeToRunExperiment: number
    RepeaterDecisionFunction: String
    ResultDataTypes: Array<String>
    ResultStructure: Array<String>
    TaskName: String
    TaskParameters: Array<String>
    WorkerConfiguration
}
interface ModelCreation {
    FeaturesLabelsStructure: Array<String>
    MinimumAccuracy: number
    ModelTestSize: number
    ModelType: String

}
interface SelectionAlgorithm {
    NumberOfInitialExperiments: Number
    SelectionType: String
}