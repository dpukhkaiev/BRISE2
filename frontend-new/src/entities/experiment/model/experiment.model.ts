export interface ExperimentDescription {
    DomainDescription?: DomainDescription
    Context: {
        TaskConfiguration: TaskConfiguration
        SearchSpace: any
    }
    TaskConfiguration?: TaskConfiguration
    Predictor?: Predictor
    SelectionAlgorithm?: SelectionAlgorithm
    ConfigurationSelection?: any
    RepetitionManager?: any
    StopCondition?: any
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
    Scenario: { ws_file: string }
    TimeUnit: string
}
interface Predictor {
    models: Array<any>
    ModelType: String
}
interface SelectionAlgorithm {
    SelectionType: String
}