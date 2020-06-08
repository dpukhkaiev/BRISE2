## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The framework settings configuration file entities explanation
Frameworks main modules should be described in 6 general topics (top-level-keys in json file) of the settings [file](./SettingsBRISE.json).
All other configurations are nested to these as key-value entities.
<details>
<summary> Description of required experiment configurations </summary>

- `General` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `isMinimizationExperiment` - `bool`. Minimization or maximization experiment
    - `EventService` - describes RabbitMQ settings.
        - `Address` - `string`. Address of RabbitMQ service.
        - `Port` - `int`. Port of RabbitMQ service for AMQP connection.

- `SelectionAlgorithm` - describes the way of search space (all possible configuration) exploration.
    - `SelectionType` - `string`. An exploration algorithm specification. Variants: `SobolSequence`, `ConfigSpaceSelector` (Mersenne Twister).

- `OutliersDetection` - the results of each Configuration run (Tasks) could differ significantly 
from other observations (Tasks) and those bias Configuration measurement results.
    This module could find these Tasks and exclude them from the Configuration results.
    *Note, that the evaluation of subsequent Configurations could change the decision made before.*

    Parameters for OutliersDetection module are described by 2 main keys: `bool` variable `isEnabled` (if `true` - OutlierDetection is switched on; if `false` - switched off ) and `Detectors` - a list of dictionaries, each of which contains two required key-value pairs:
    - `Type` - `string` - the name of Outlier Detection criterion (a.k.a. test or detector). Variants: `Dixon`, `Chauvenet`, `MAD`, `Grubbs`, `Quartiles`.
    - `Parameters` - `dictionary` - a set of key-value parameters used by specified in `Type` criterion.

    Current implementation of OutlierDetection module supports 5 detectors to distinguish whether the Task is an outlier or not.
    - `Dixon` - Dixon test calculates the distance between a suspicious value and the closest one to it, then the
     received value is divided by a distance between min and max value in the sample and is checked in coefficient table.
    - `Chauvenet` - The idea behind Chauvenet's criterion is to find a probability band, centered on the mean of a 
    normal distribution, that should reasonably contain all n samples of a data set.
    - `MAD` - It is the median of the set comprising the absolute values of the differences between the median and each data point.
    - `Grubbs` - The test finds if a minimum value or a maximum value is an outlier.
    - `Quartiles` - This test splits data into quartiles, then finds interquartile distance. All values, that goes beyond (Q1-3*IQR : Q3+3*IQR) are outliers.

    Each of the aforementioned criteria could be enabled by including it into the Experiment Description with two required parameters:
    - `MinActiveNumberOfTasks` - `int` - a minimum number of Tasks in Configuration to enable criterion.
    - `MaxActiveNumberOfTasks` - `int` - a maximum number of Tasks in Configuration while the criterion still works. 
    In case of exceeding this boundary, the criterion will be disabled. The string value `"Inf"` is supported.
    
    The reason for specifying the boundaries is in a suitability of each test for different amount and structure of data.
    In case of enabling several criteria, the Task will be marked as *Outlier* if at least a half of tests mark the Task as an *Outlier*.

- `Repeater` (Repetition Manager) - Results of each Configuration evaluation could not be precise/deterministic. 
The intent of the Repetition Manager is to ensure statistical significance of each Configuration evaluation by running it several times (Tasks).
    - `Type` - `string` - a type of a Repetition Manager represents a strategy to check the accuracy of the 
    Configuration measurement. Variants: `QuantityBased`, `AcceptableErrorBased`
        - `QuantityBased` - evaluates Configuration *MaxTasksPerConfiguration* times. Required parameters:
            - `MaxTasksPerConfiguration` - a maximum number of times to evaluate (run) each Configuration.
        - `AcceptableErrorBased` - checks the overall absolute deviation between Tasks and takes into account
         the Configuration quality (how close it is to the currently best Configuration found). Required parameters:
            - `MinTasksPerConfiguration` - `int` - a minimum number of repetitions to evaluate (run) each Configuration.
            - `MaxTasksPerConfiguration` - `int` - a maximum number of repetitions to evaluate (run) each Configuration.
             After reaching this amount new Tasks will not be added to the Configuration.
            - `BaseAcceptableErrors` - `array of floating point numbers` - A starting value for an acceptable Relative Error 
            for each dimension in result.
            - `ConfidenceLevels` - `array of floating point numbers 0..1` - Probabilities, that Configuration results 
            (each dimension) will appear in a boundary of an Acceptable Relative error.
            - `DevicesScaleAccuracies` - `array of floating point numbers` - A minimal value on a device scale, 
            that is possible to distinguish for each dimension in results.
            - `DevicesAccuracyClasses` - `array of integers` - Accuracy classes of devices that is used to 
            estimate each dimension of the result.
            - `ExperimentAwareness` - `boolean` - Is Repeater is in experiment-aware mode? If yes (`true`), 
            the following parameters are obligatory:
                - `MaxAcceptableErrors` - `array of floating point numbers` - A maximal value for the Acceptable Relative 
                errors, used if the Repeater is experiment-aware.
                - `RatiosMax` - `array of floating point numbers` - A relation between current solution Configuration 
                and current Configuration, when Relative error threshold will reach MaxAcceptableErrors value. 
                Specified separately for each dimension in a results.
            
    - *To disable the repetition management* (if the target algorithm is deterministic or 
    Configuration evaluation is considered precise) set `MaxTasksPerConfiguration` equal to `1` and `Type` to `QuantityBased`.
    - To get more information on Repetition Manager, please consult with a corresponding [README](./../repeater/README.md)  
 
     
- `ModelConfiguration` - section with the configuration related to the surrogate prediction model creating process.
    - `SamplingSize` - `int`. A number of configurations that should be sampled from a continuous search space in 
    order to give the model enough information for prediction. Obligatory for all prediction models.
    - `ModelType` - `string`. Type of the surrogate prediction model. *Variants:* 
        - `BO` - Bayesian Optimization model (using the Tree Parzen Estimator or TPE).
        - `regression` - Polynomial regression model. For this prediction model the following additional parameters are obligatory:
            - `minimalTestingSize` - `float`. A minimum possible fraction that specifies an amount of data for testing the created prediction model.
            - `maximalTestingSize` - `float`. A fraction that specifies an amount of data for testing the created prediction model.
            - `MinimumAccuracy` - `float`. A minimum accuracy that model should provide before making any predictions/testing.
        
- `StopConditionTriggerLogic` - The user could specify any logic of BRISE Experiment termination by composing the operands 
`and`, `or`, brackets `(` `)` and names of Stop Conditions into a single expression.
- `StopCondition` - termination criteria of BRISE Experiment.
    - `Stop Condition Name` - `String` Name of the Stop Condition which plays roll of an ID. Should be unique.  
    - `Stop Condition Type` - `String` Strategy used for BRISE Experiment termination. *Variants (with parameters)*
        - `QuantityBased` - `String` Stop when the specified number of configuration was measured.
            `MaxConfigs` - `Int` Maximum number of measured configurations. 
        - `ValidationBased` - `String` Stop if the valid model was built.
        - `ImprovementBased` - `String` - Stop in case of a newly evaluated Configuration is better, than the Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - Terminate after this number of Configurations were evaluated 
            and no better was found.
        - `Adaptive` - `String`- Stop if no improvement got for the current solution after a specified percentage of 
        the search space evaluated.
            - `SearchSpacePercentage` - `Int` - % of the Configuration search space evaluated.
        - `Guaranteed` - `String` - The BRISE Experiment is stopped if such configuration is found, that is better than the Default configuration.
        - `TimeBased` - `String` - Launches a user-defined timer. The BRISE Experiment will stop when time is over.
        Required parameters:
            - `MaxRunTime` - `Int` - Time value for the timer.
            - `TimeUnit` - `String` - Time unit for the timer (seconds, minutes etc).
        - `BadConfigurationBased` - `String` - The BRISE Experiment will stop in case of reaching a threshold of failed Configurations number.
        Required parameters:
            - `MaxBadConfigurations` - `Int` - Threshold of failed Configurations. Failed configuration should not contain any correct Tasks.
###### Note: Stop Conditions, that are defined in `StopCondition` block, but not used in `StopConditionTriggerLogic` block will be ignored.
</details>

### Experiment Description and Experiment Data entities explanation
Parameters related to the experiment inputs/outputs should be described in 2 general topics (top-level-keys in json file) of the Experiment Description file.
All other configurations are nested to these as key-value entities.

Possible values of configurations for your system should be provided in Experiment Data file.
<details>
<summary> Description of required experiment configurations </summary>

- `DomainDescription` - describes what configurations the target system uses. 
Value - `dictionary` with following key-value pairs.
    - `HyperparameterNames` - `list of strings`. The names of configurations.
    - `DataFile` - `string`. Path to json file with all possible values of all configurations.
    - `DefaultConfigurationHandler`. Optional parameter. If a default configuration is not specified or specified 
    incorrectly, random configuration is picked instead. This module can be extended to provide a specific logic.

- `TaskConfiguration` - describes experiment- and target-system-specific parameters.
    - `TaskName` - `string`. Name of the target system to be identified by the Worker nodes.
    - `Scenario` - `dict`. Specific problem instance which is to solved by the target system.
    - `TaskParamenters` - `List of strings`. List of parameters that form the search space.
    - `ResultStructure` - `List of strings`. A list of metric that the target system reports back.
    - `ResultDataTypes` - `List of strings`. Python data types of the target system output metrics.
    - `ExpectedValuesRange` - `List`. A list of ranges containing the expected/meaningful results for each metric the target system returns.
    - `MaxTimeToRunTask` - `float`. Maximum time to run each task in seconds. In case of exceeding this threshold the task will be terminated.
</details>

#### We provide a validation of the Experiment Description file using JSON-Schema.
* The project JSON-Schema could be found [here](./schema/experiment.schema.json).
* An example of valid framework settings file could be found [here](./SettingsBRISE.json).
* An example of valid Experiment Description file could be found [here](./EnergyExperiment.json).
* The related Domain Description Data file could be found [here](./EnergyExperimentData.json).

<details>
<summary> Example of framework settings file </summary>

```json
{
  "General":{
    "isMinimizationExperiment"  : true,
    "EventService": {
      "Address": "event-service",
      "Port" : 49153
    }
  },
  "SelectionAlgorithm":{
    "SelectionType"     : "SobolSequence"
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
    "Type": "AcceptableErrorBased",
    "Parameters": {
      "MaxFailedTasksPerConfiguration": 5,
      "MaxTasksPerConfiguration": 10,
      "MinTasksPerConfiguration": 2,
      "BaseAcceptableErrors": [5],
      "ConfidenceLevels": [0.95],
      "DevicesScaleAccuracies": [0],
      "DevicesAccuracyClasses": [0],
      "ExperimentAwareness":{
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
  "StopConditionTriggerLogic":{
    "Expression": "(QuantityBased and Guaranteed and ImprovementBased and ValidationBased) or BadConfigurationBased or TimeBased",
    "InspectionParameters":{
      "RepetitionPeriod": 1,
      "TimeUnit": "seconds"
    }
  },
  "StopCondition":[
    {
      "Type": "QuantityBased",
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
      "Type": "Guaranteed",
      "Parameters": {      }
    },
    {
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
      }
    },
    {
      "Type": "TimeBased",
      "Parameters":{
        "MaxRunTime": 10,
        "TimeUnit": "minutes"
      }
    },
    {
      "Type": "ValidationBased",
      "Parameters": {      }
    }
  ]
}

```
</details>

<details>
<summary> Example of Experiment configuration file </summary>

```json
{
  "DomainDescription":{
    "HyperparameterNames"      : ["frequency", "threads"],
    "DataFile"          : "./Resources/EnergyExperimentData.json"
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
  }
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
