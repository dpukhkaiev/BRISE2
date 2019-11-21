## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The configuration files entities explanation
Process of finding (near)optimal configuration of target system should be described in 7 general topics (top-level-keys in json file) of the configuration file.
All other configurations are nested to these as key-value entities.

Possible values of configurations for your system should be provided in separate json file (which is further called "data file").
<details>
<summary> Description of required experiment configurations </summary>

- `General` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `isMinimizationExperiment` - `bool`. Minimization or maximization experiment
    - `ConfigurationsPerIteration` - `int`. The number of configurations that will be measured simultaneously. **optional**

- `DomainDescription` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `HyperparameterNames` - `list of strings`. The names of configurations.
    - `DataFile` - `string`. Path to json file with all possible values of all configurations.
    - `DefaultConfigurationHandler`. Optional parameter. If default configuration is not specified or specified incorrectly, random configuration can be picked inhstead or other specific handler can be used

- `SelectionAlgorithm` - describes the way of search space (all possible configuration) exploration.
    - `SelectionType` - `string`. An exploration algorithm specification. Currently only `SobolSequence` available.
    - `NumberOfInitialConfigurations` - `int`. The number of configurations that will be tested before making any attempts to build prediction model.

- `TaskConfiguration` - this section describes general configuration for Worker Service and your system during testing.
    - `TaskName` - `string`. The Worker nodes are able to run different experiments/tasks. This value identifies needed.
    - `Scenario` - `dict`. the experiments/tasks configuration that is static and is needed to be passed to Worker nodes each time.
    - `TaskParamenters` - `List of strings`. Configurations that the Worker nodes will use to run target system.
    - `ResultStructure` - `List of strings`. Configurations that the Worker nodes will report back to Main node. `TaskParameters` should be included. 
    - `ResultDataTypes` - `List of strings`. Should be a proper names of Python data types, used for casting data that arrives from Worker nodes (as strings).
    - `ExpectedValuesRange` - `List`. The range of expected tasks' results for the current experiment
    - `MaxTimeToRunTask` - `float`. Maximum time to run each task in seconds. In case of exceeding the task will be terminated.

- `OutliersDetection` - the results of each Configuration run (Tasks) could differ significantly from other observations (Tasks) and those bias Configuration measurement results.
    This module could find these Tasks and exclude them from the Configuration results.
    *Note that appearance of new Tasks could change the decision made before.*

    The parameters for OutliersDetection module appear as a list of dictionaries, each of them contains two required key-value pairs:
    - `Type` - `string` - the name of Outlier Detection criterion (a.k.a. test or detector). Variants: `Dixon`, `Chauvenet`, `MAD`, `Grubbs`, `Quartiles`.
    - `Parameters` - `dictionary` - a set of key-value parameters used by specified in `Type` criterion.

    Current implementation of OutlierDetection module supports 5 detectors to distinguish whether the Task is Outlier or not.
    - `Dixon` - Dixon test calculates distance between suspicious value and closest one to it, then received value is divided on distance between min and max value in sample and checks this value in coefficient table.
    - `Chauvenet` - The idea behind Chauvenet's criterion is to find a probability band, centered on the mean of a normal distribution, that should reasonably contain all n samples of a data set.
    - `MAD` - It is the median of the set comprising the absolute values of the differences between the median and each data point.
    - `Grubbs` - The test finds if a minimum value or a maximum value is an outlier.
    - `Quartiles` - This test splits data into quartiles, then finds interquartile distance. All values, that goes beyond (Q1-3*IQR : Q3+3*IQR) are outliers.

    Each of described above criteria could be enabled by including it to the Experiment Description with two required parameters:
    - `MinActiveNumberOfTasks` - `int` - a minimum number of Tasks in Configuration to enable criterion.
    - `MaxActiveNumberOfTasks` - `int` - a maximum number of Tasks in Configuration while the criterion still works. In case of exceeding this boundary, the criterion will be disabled. The string value `"Inf"` is supported.

    This was done while each test is suitable for different amount and structure of available data.
    In case of enabling several criteria, the Task will be marked as *Outlier* if at least half of tests mark the Task as *Outlier*.

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
    - `SamplingSize` - `int`. A number of configurations that should be sampled from a continuous search space in order to give model enough information for prediction.
    - `ModelType` - `string`. Type of heuristic prediction model. *Variants:* 
        - `regression` - Polynomial regression model.
        - `BO` - Bayesian Optimization model (using the Tree Parzen Estimator or TPE).

- `StopCondition` - when to stop BRISE.
    - `Stop Condition Name` - `String` Strategy used for BRISE termination. *Variants (with parameters)*
        - `Default` - `String`(key, value - parameters for Stop Condition (as a nested dictionary)) - The BRISE will stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - ? (need to refine this description).
        - `ImprovementBased` - `String` - The BRISE could (but don't have to) stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - Terminate after this amount of Configurations were tested and no better found. (but still, better than default was found).
        - `Adaptive` - `String`- Stop if no improvement got for current solution after some percentage of overall Configuration search space evaluation.
            - `SearchSpacePercentageWithoutImprovement` - `Int` - % of the Configuration search space evaluated without improvement.
        - `Guaranteed` - `String` - The BRISE is stopped if such configuration is found, that is better than default one
        - `TimeBased` - `String` - Launches user-defined timer. The BRISE will stop when time is over.
        Required parameters:
            - `MaxRunTime` - `Int` - Time value for timer.
            - `TimeUnit` - `String` - Time unit for timer (seconds, minutes etc).
        - `BadConfigurationBased` - `String` - The BRISE will stop in case of reaching threshold of failed Configurations number.
        Required parameters:
            - `MaxBadConfigurations` - `Int` - Threshold of failed Configurations. Failed configuration should not contain any correct measurings.
</details>

#### We provide validation of the Experiment Description file using JSON-Schema.
* The project JSON-Schema could be found [here](./schema/experiment.schema.json).
* An example of valid Experiment Description file could be found [here](./EnergyExperiment.json).
* The related Domain Description Data file could be found [here](./EnergyExperimentData.json).

<details>
<summary> Example of Experiment configuration file </summary>

```json
{
  "General":{
    "isMinimizationExperiment"  : true,
    "ConfigurationsPerIteration" : 3
  },
  "DomainDescription":{
    "HyperparameterNames"      : ["frequency", "threads"],
    "DataFile"          : "./Resources/EnergyExperimentData.json"
  },
  "SelectionAlgorithm":{
    "SelectionType"     : "SobolSequence",
    "NumberOfInitialConfigurations": 10
  },
  "TaskConfiguration":{
    "TaskName"          : "energy_consumption",
    "Scenario":{
      "ws_file": "Radix-500mio.csv"
    },
    "TaskParameters"   : ["frequency", "threads"],
    "ResultStructure"   : ["energy"],
    "ResultDataTypes"  : ["float"],
    "ExpectedValuesRange": [[0, 150000]],
    "MaxTimeToRunTask": 10
  },
  "OutliersDetection":[
    {
      "Type": "Dixon",
      "Parameters": {
        "MinActiveNumberOfTasks": 3,
        "MaxActiveNumberOfTasks": 30
      }
    },
    {
      "Type": "Chauvenet",
      "Parameters": {
        "MinActiveNumberOfTasks": 3,
        "MaxActiveNumberOfTasks": 10000
      }
    }
  ],
  "Repeater":{
    "Type": "student_deviation",
    "Parameters": {
      "MaxFailedTasksPerConfiguration": 5,
      "MaxTasksPerConfiguration": 10,
      "MinTasksPerConfiguration": 2,
      "BaseAcceptableErrors": [5],
      "ConfidenceLevels": [0.95],
      "DevicesScaleAccuracies": [0],
      "DevicesAccuracyClasses": [0],
      "ModelAwareness": {
        "isEnabled": true,
        "MaxAcceptableErrors": [50],
        "RatiosMax": [10]
      }
    }
  },
  "ModelConfiguration":{
    "SamplingSize": 96,
    "ModelType"         : "BO"
  },
  "StopCondition":[
    {
      "Type": "Default",
      "Parameters": {
        "MaxConfigs": 15
      }
    },
    {
      "Type": "ImprovementBased",
      "Parameters": {
        "MaxConfigsWithoutImprovement": 5
      }
    },
    {
      "Type": "TimeBased",
      "Parameters": {
        "MaxRunTime": 10,
        "TimeUnit": "minutes"
      }
    },
    {
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
      }
    }
  ]
}

```
</details>

<details>
<summary> Example of Experiment data file </summary>

```json
{
  "hyperparameters": [
    {
      "name": "threads",
      "type": "categorical",
      "choices": [1, 2, 4, 8, 16, 32],
      "default": 32
    },
    {
      "name": "frequency",
      "type": "categorical",
      "choices": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
        2900.0, 2901.0],
      "default": 2900.0
    }
  ],
  "conditions": [],
  "forbiddens": []
}
```

</details>

<details>
<summary> Artificial example of Experiment data file (demonstration of all features) </summary>

```json
{
  "hyperparameters": [
    {
      "name": "number_of_trees",
      "type": "uniform_int",
      "log": false,
      "lower": 2,
      "upper": 500,
      "default": 500
    },
    {
      "name": "subset_ratio",
      "type": "uniform_float",
      "log": false,
      "lower": 0.0,
      "upper": 1.0,
      "default": 0.3
    },
    {
      "name": "use_local_random_seed",
      "type": "categorical",
      "choices": [
        "true",
        "false"
      ],
      "default": "false"
    },
    {
      "name": "local_random_seed",
      "type": "uniform_int",
      "log": false,
      "lower": 1992,
      "upper": 1998,
      "default": 1992
    }
  ],
  "conditions": [
    {
      "child": "local_random_seed",
      "parent": "use_local_random_seed",
      "type": "EQ",
      "value": "true"
    }
  ],
  "forbiddens": [
    {
      "name": "number_of_trees",
      "type": "AND",
      "clauses": [
        {
          "name": "number_of_trees",
          "type": "EQUALS",
          "value": 2
        },
        {
          "name": "subset_ratio",
          "type": "IN",
          "values": [0.1, 0.2]
        }
      ]
    }
  ]
}	
```
</details>

#### Validate the configuration file:
* For validation JSON documents use [json-schema](https://json-schema.org/)
* Useful examples. [Understanding-json-schema] (https://json-schema.org/understanding-json-schema/index.html)
