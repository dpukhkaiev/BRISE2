## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The configuration files entities explanation
Process of finding (near)optimal configuration of target system should be described in 4 general topics (top-level-keys in json file) of the configuration file.
All other configurations are nested to these as key-value entities.

Possible values of configurations for your system should be provided in separate json file.

**All specified here configurations are required.**

- `General` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `isMinimizationExperiment` - `bool`. Minimization or maximization experiment
    - `ConfigurationsPerIteration` - `int`. The number of configurations that will be measured simultaneously. **optional**

- `DomainDescription` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `FeatureNames` - `list of strings`. The names of configurations.
    - `DataFile` - `string`. Path to json file with all possible values of all configurations. 
    - `AllConfigurations` - here will be loaded configurations from the `DataFile`.
    - `DefaultConfiguration` - `list of values`. **an order must match the `FeatureNames`**. User`s assumption about a default configuration that system uses.

- `SelectionAlgorithm` - describes the way of search space (all possible configuration) exploration.
    - `SelectionType` - `string`. An exploration algorithm specification. Currently only `SobolSequence` available.
    - `NumberOfInitialConfigurations` - `int`. The number of configurations that will be tested before making any attempts to build prediction model.

- `TaskConfiguration` - this section describes general configuration for Worker Service and your system during testing.
    - `TaskName` - `string`. The Worker nodes are able to run different experiments/tasks. This value identifies needed.
    - `WorkerConfiguration` - `dict`. the experiments/tasks configuration that is static and is needed to be passed to Worker nodes each time.
    - `TaskParamenters` - `List of strings`. Configurations that the Worker nodes will use to run target system.
    - `ResultStructure` - `List of strings`. Configurations that the Worker nodes will report back to Main node. `TaskParameters` should be included. 
    - `ResultDataTypes` - `List of strings`. Should be a proper names of Python data types, used for casting data that arrives from Worker nodes (as strings).
    - `MaxTimeToRunTask` - `float`. Maximum time to run each task in seconds. In case of exceeding the task will be terminated.

- `RepeaterConfiguration` - Results of each Configuration evaluation could not be precise/deterministic. The intent of Repeater is to reduce the variance between the evaluation of each Configuration by running it several times (Tasks).
    - `Type` - `string` - a type of repeater represents a strategy to check the accuracy of the Configuration measurement. Variants: `default`, `student_deviation`
        - `default` - evaluates Configuration *MaxTasksPerConfiguration* times. Required parameters:
            - `MaxTasksPerConfiguration` - a maximum number of times to evaluate (run) each Configuration.
        - `student_deviation` - checks the overall absolute deviation between Tasks and takes into account the Configuration quality (how close it is to the currently best Configuration found). Required parameters:
            - `MinTasksPerConfiguration` - `int` - a minimum number of repetitions to evaluate (run) each Configuration.
            - `MaxTasksPerConfiguration` - `int` - a maximum number of repetitions to evaluate (run) each Configuration. After reaching this amount new Tasks will not be added to the Configuration.
            - `BaseAcceptableErrors` - `array of floating numbers` - A starting value for an acceptable Relative Error for each dimension in result.
            - `ConfidenceLevels` - `array of floating numbers 0..1` - Probabilities, that Configuration results (each dimension) will appear in a boundary of an Acceptable Relative error.
            - `DevicesScaleAccuracies` - `array of floating numbers` - A minimal value on a device scale, that is possible to distinguish for each dimension in results.
            - `DevicesAccuracyClasses` - `array of integers` - Accuracy classes of devices that is used to estimate each dimension of the result.
            - `ModelAware` - `boolean` - Is Repeater is in model-aware mode? If yes (`true`), the following parameters are obligatory:
                - `MaxAcceptableErrors` - `array of floating numbers` - A maximal value for the Acceptable Relative errors, used if the Repeater is model-aware.
                - `RatioMax` - `array of floating numbers` - A relation between current solution Configuration and current Configuration, when Relative error threshold will reach MaxAcceptableErrors value. Specified separately for each dimension in a results.
            
    - *To disable repeater* (if the target algorithm is deterministic or Configuration evaluation considered precise) set `MaxTasksPerConfiguration` equal to `1` and `Type` to `default`.
 
     
- `ModelConfiguration` - section with the configuration related to the prediction model creating process.
    - `minimalTestingSize` - `float`. A minimum possible fraction that specifies an amount of data for testing the created prediction model.
    - `maximalTestingSize` - `float`. A fraction that specifies an amount of data for testing the created prediction model.
    - `MinimumAccuracy` - `float`. A minimum accuracy that model should provide before making any predictions/testing.
    - `ModelType` - `string`. Type of heuristic prediction model. *Variants:* 
        - `regression` - Polynomial regression model.
        - `BO` - Bayesian Optimization model (using the Tree Parzen Estimator or TPE).

- `StopCondition` - when to stop BRISE.
    - `Stop Condition Name` - `String` Strategy used for BRISE termination. *Variants (with parameters)*
        - `default` - `String`(key, value - parameters for Stop Condition (as a nested dictionary)) - The BRISE will stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - ? (need to refine this description).
        - `improvement_based` - `String` - The BRISE could (but don't have to) stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - Terminate after this amount of Configurations were tested and no better found. (but still, better than default was found).
        - `adaptive` - `String`- Stop if no improvement got for current solution after some percentage of overall Configuration search space evaluation.
            - `SearchSpacePercentageWithoutImprovement` - `Int` - % of the Configuration search space evaluated without improvement.

#### Example of configuration file:
```json
{
      "General":{
        "isMinimizationExperiment"  : true
      },
      "DomainDescription":{
        "FeatureNames"      : ["frequency", "threads"],
        "DataFile"          : "./Resources/EnergyExperimentData.json",
        "AllConfigurations"    : "# Will be loaded from DataFile and overwritten",
        "DefaultConfiguration": [2900.0, 32]
      },
      "SelectionAlgorithm":{
        "SelectionType"     : "SobolSequence",
        "NumberOfInitialConfigurations": 10
      },
      "TaskConfiguration":{
        "TaskName"          : "energy_consumption",
        "WorkerConfiguration":{
          "ws_file": "Radix-500mio.csv"
        },
        "TaskParameters"   : ["frequency", "threads"],
        "ResultStructure"   : ["energy"],
        "ResultDataTypes"  : ["float"],
        "MaxTimeToRunTask": 10
      },
      "Repeater":{
        "Type": "student_deviation",
        "Parameters": {
          "MaxTasksPerConfiguration": 10,
          "MinTasksPerConfiguration": 2,
          "BaseAcceptableErrors": [10],
          "ConfidenceLevels": [0.95],
          "DevicesScaleAccuracies": [0],
          "DevicesAccuracyClasses": [0],
          "ModelAwareness": {
            "isEnabled": true,
            "MaxAcceptableErrors": [70],
            "RatiosMax": [10]
          }
        }
      },
      "ModelConfiguration":{
        "ModelType"         : "BO"
      },
      "StopCondition": {
        "adaptive": {
          "SearchSpacePercentageWithoutImprovement": 10
        }
      }
}
```

#### Example of Experiment data file:
```json
{
    "threads": [1, 2, 4, 8, 16, 32],
    "frequency": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
      2900.0, 2901.0]
}
```

#### Validate the configuration file:
* For validation JSON documents use [json-schema](https://json-schema.org/)
* Useful examples. [Understanding-json-schema] (https://json-schema.org/understanding-json-schema/index.html)
