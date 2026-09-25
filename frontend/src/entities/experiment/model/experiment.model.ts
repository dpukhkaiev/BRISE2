export interface ExperimentDescription {
    DomainDescription?: DomainDescription
    Context: {
        TaskConfiguration: TaskConfiguration
        SearchSpace: unknown
    }
    TaskConfiguration?: TaskConfiguration
    Predictor?: Predictor
    SelectionAlgorithm?: SelectionAlgorithm
    ConfigurationSelection?: unknown
    RepetitionManager?: unknown
    StopCondition?: unknown
    PlotSelection?: PlotSelection
}

interface DomainDescription {
    DataFile: String
}

interface PlotSelection {
    Plot?: Record<string, unknown>
}

export interface SurrogateModel {
  ConfigurationTransformers?: Record<string, any>
  Instance?: {
    LinearRegression?: {
      MultiObjective?: boolean
      Type?: string
      Class?: string
    }
    [key: string]: any
  }
}

interface TaskConfiguration {
    MaxTasksPerConfiguration: number
    MaxTimeToRunTask: number
    RepeaterDecisionFunction?: string
Objectives: Record<string, Objective>
    ObjectivesDataTypes: Array<string>
    ObjectivesPriorities: Array<number>
    TaskName: string
    Scenario: unknown
    TimeUnit: string
}


interface Objective {
    Name: string
    DataType: string
    Minimization: boolean
    MinExpectedValue?: number
    MaxExpectedValue?: number
}
interface Predictor {
    models: Array<any>
    ModelType: String
}
interface SelectionAlgorithm {
    SelectionType: String
}