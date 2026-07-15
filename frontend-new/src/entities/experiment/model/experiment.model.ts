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
    PlotSelection: any
}

interface DomainDescription {
    DataFile: String
}
interface TaskConfiguration {
    MaxTasksPerConfiguration: number
    MaxTimeToRunTask: number
    RepeaterDecisionFunction: string
    Objectives: Array<string>
    ObjectivesDataTypes: Array<string>
    ObjectivesPriorities: Array<number>
    TaskName: string
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