export interface ExperimentDescription {
    DomainDescription?: DomainDescription
    Context: {
        TaskConfiguration: TaskConfiguration
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

// a parameter of the search space as main-node describes it (SearchSpace.describe_regions()); Inactive is the value
// that stands for the parameter in a configuration where it is not active
export interface ParameterSpec {
    Name: string
    Type: string
    Level: number
    Categories?: string[]
    Lower?: number
    Upper?: number
    Inactive: string | number
}

// the parameters that are activated together; the ActivationCategory is 'root' for the top-level ones
export interface SearchSpaceRegion {
    ActivationCategory: string
    Parameters: ParameterSpec[]
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