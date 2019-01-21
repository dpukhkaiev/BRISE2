## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The configuration files entities explanation
Process of finding (near)optimal configuration of target system should be described in 4 general topics (top-level-keys in json file) of the configuration file.
All other configurations are nested to these as key-value entities.

Possible values of configurations for your system should be provided in separate json file.

**All specified here configurations are required.**

- `DomainDescription` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `FeatureNames` - `list of strings`. The names of configurations.
    - `DataFile` - `string`. Path to json file with all possible values of all configurations. 
    - `AllConfigurations` - here will be loaded configurations from the `DataFile`.
    - `DefaultConfiguration` - `list of values`. **an order must match the `FeatureNames`**. User`s assumption about a default configuration that system uses.

- `SelectionAlgorithm` - describes the way of search space (all possible configuration) exploration.
    - `SelectionType` - `string`. An exploration algorithm specification. Currently only `SobolSequence` available.
    - `NumberOfInitialConfigurations` - `int`. The number of configurations that will be tested before making any attempts to build prediction model.
    - `Step` - `int`. The number of configurations that will be tested simultaneously.

- `TaskConfiguration` - this section describes general configuration for Worker Service and your system during testing.
    - `TaskName` - `string`. The Worker nodes are able to run different experiments/tasks. This value identifies needed.
    - `WorkerConfiguration` - `dict`. the experiments/tasks configuration that is static and is needed to be passed to Worker nodes each time.
    - `TaskParamenters` - `List of strings`. Configurations that the Worker nodes will use to run target system.
    - `ResultStructure` - `List of strings`. Configurations that the Worker nodes will report back to Main node. `TaskParameters` should be included. 
    - `ResultDataTypes` - `List of strings`. Should be a proper names of Python data types, used for casting data that arrives from Worker nodes (as strings).
    - `RepeaterDecisionFunction` - `string`. Each experiments should be repeated to exclude a fluctuations in the results. Possible values - `student_deviation`(repeat the experiment, until absolute error higher that a threshold), `default` - just repeat the experiment maximum times.
    - `MaxRepeatsPerConfiguration` - `int`. Maximum times to run each configuration. 
    - `MaxTimeToRunTask` - `float`. Maximum time to run each task in seconds. In case of exceeding the task will be terminated.
    
- `ModelConfiguration` - section with the configuration related to the prediction model creating process.
    - `ModelTestSize` - `float`. A fraction that specifies an amount of data for testing the created prediction model.
    - `MinimumAccuracy` - `float`. A minimum accuracy that model should provide before making any predictions/testing.
    - `ModelType` - `string`. Type of prediction model. Currently available `regression`.
       

#### Example of configuration file:
```json
{
      "DomainDescription":{
        "FeatureNames"      : ["frequency", "threads"],
        "DataFile"          : "./Resources/taskData.json",
        "AllConfigurations"    : "# Will be loaded from DataFile and overwritten",
        "DefaultConfiguration": [2900.0, 32]
      },
      "SelectionAlgorithm":{
        "SelectionType"     : "SobolSequence",
        "NumberOfInitialConfigurations"   : 10,
        "Step"              : 1
      },
      "TaskConfiguration":{
        "TaskName"          : "energy_consumption",
        "WorkerConfiguration":{
          "ws_file": "Radix-500mio.csv"
        },
        "TaskParameters"   : ["frequency", "threads"],
        "ResultStructure"   : ["energy"],
        "ResultDataTypes"  : ["float"],
        "RepeaterDecisionFunction"  : "student_deviation",
        "MaxTasksPerConfiguration": 10,
        "MaxTimeToRunTask": 10
      },
      "ModelConfiguration":{
        "ModelTestSize"     : 0.9,
        "MinimumAccuracy"   : 0.85,
        "ModelType"         : "BO",
        "isMinimizationExperiment"  : true
      },
      "StopCondition": {
        "adaptive": {
          "SearchSpacePercentageWithoutImprovement": 10
        }
      }
}
```

#### Example of data file:
```json
{
    "threads": [1, 2, 4, 8, 16, 32],
    "frequency": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
      2900.0, 2901.0]
}
```

#### Validate the configuration file:
Run `is_experiment_description_valid()` from `\main-node\Resources\validator.py`
If necessary, use committed code