## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The framework settings configuration file entities explanation
Framework's configuration should be described with 7 general facets (top-level-keys in json file) of the settings [file](./SettingsBRISE.json).
All other configurations are nested to these as key-value entities.
<details>
<summary> Description of the required experiment configuration </summary>

- `General` - a system-related configuration. Value - `dictionary` with following key-value pairs.
    - `EventService` - describes RabbitMQ settings.
        - `Address` - `string`. Address of RabbitMQ service.
        - `Port` - `int`. Port of RabbitMQ service for AMQP connection.

- `SelectionAlgorithm` - model-independent sampling strategy. Variants: `SobolSequence`, `MersenneTwister`.

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
 
     
- `Predictor` - surrogate model creation process.
    - `window size` - `float` or `int`. A number of already evaluated configurations that should be used to create the surrogate model: 
    `float` to specify the window size as a percentage from configurations or integer to specify an exact value. 
    - `models` - `array of objects`. Array of models, which will be used at each level of the search space.
    Each model configuration requires two fields, `Type` and `Parameters`:
        - `Type` - `string`. A name of the model to use on this level. Based on the name, BRISE will import required model. 
        The name is structured from two parts, separated by `.`, for instance: `brise.TreeParzenEstimator`. 
        The first part (e.g., *brise*, *sklearn*) specifies where to import model from. 
        Allowed values are: 
            - `brise` - model will be imported from [model](./../model) folder.
            - `sklearn` - will be imported one of [Scikit-learn](https://scikit-learn.org/) linear models.
        The second part is the name of the model. Allowed values depends on the source of the model:
                - for `brise` the allowed values are: `TreeParzenEstimator`, `MultiArmedBandit` and `ModelMock` (randomly samples parameters).
                - for `sklearn` see the list of models [here](https://scikit-learn.org/stable/modules/classes.html#module-sklearn.linear_model).
        - `Parameters` - `object`. Specifies parameter values for each model, depending on the model type.
        Shared parameters:
            - `SamplingSize` - `int`, defines the number of random configurations sampled to optimize the surrogate model.
            - `DataPreprocessing` - `object`, defines which preprocessing methods to use for specific data type.

            For brise-provided models please see corresponding constructor.
            For Scikit-learn models parameters follow predefined structure and require following values:
            - `CrossValidationSplits` - `int`, defines the number of re-shuffling and splitting iterations for cross-validation.
            - `TestSize`- `float or int`,  if `float`, should be between 0.0 and 1.0 and represent the proportion 
            of the dataset to include in the test split. If `int`, represents the absolute number of test samples.
            - `MinimalScore` - `float` between 0.0 and 1.0 is the accuracy threshold of created model.
            If the accuracy is below the threshold, model is not created.
            - The parameters for underlying linear scikit-learn model is passed as key-value pairs into nested `UnderlyingModelParameters` object.
       
<details>
<summary> Examples of predictor configurations. </summary>

Using BRISE FRAMAB on 1st level and TPE on second:
```json
{
"Predictor": {
  "window size": 0.8,
  "models": [
    {
      "Type": "brise.MultiArmedBandit",
      "Parameters": { "c": "std" }
    },
    {
      "Type": "brise.TreeParzenEstimator",
      "Parameters": {
        "top_n_percent": 30,
        "random_fraction": 0,
        "bandwidth_factor": 3,
        "min_bandwidth": 0.001,
        "SamplingSize": 96
      }
     }
  ]
}}
```

Using Scikit-learn Bayesian Ridge regression model:
```json
{
  "Predictor": {
    "window size": 0.8,
    "models": [
      {
        "Type": "sklearn.BayesianRidge",
        "Parameters": {
          "SamplingSize": 96,
          "MinimalScore": 0.5,
          "CrossValidationSplits": 5,
          "TestSize": 0.30,
          "DataPreprocessing": {
            "OrdinalHyperparameter": "sklearn.OrdinalEncoder",
            "NominalHyperparameter": "brise.BinaryEncoder",
            "IntegerHyperparameter": "sklearn.MinMaxScaler",
            "FloatHyperparameter": "sklearn.MinMaxScaler"
          },
          "UnderlyingModelParameters": {
            "n_iter": 200,
            "tol": 1e-2,
            "normalize": true
          }
        }
      }
   ]
 }
}
```
</details>
        
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
    - `DataFile` - `string`. Path to json file with all possible values of all configurations.
    - `DefaultConfigurationHandler`. Optional parameter. If a default configuration is not specified or specified 
    incorrectly, random configuration is picked instead. This module can be extended to provide a specific logic.

- `TaskConfiguration` - describes experiment- and target-system-specific parameters.
    - `TaskName` - `string`. Name of the target system to be identified by the Worker nodes.
    - `Scenario` - `dict`. Specific problem instance which is to solved by the target system.
        - The following fields should be specified for Hyper-heuristic mode (TaskName = `tsp_hh_flat`):
            - `Problem` - `string`. Name of optimization problem type. Supported `TSP`.
            - `problem_initialization_parameters` - `Mapping`. Parametrizes the optimization problem:
                - `instance` - `string`. Path to the problem description file in worker node. For instance `scenarios/tsp/kroA100.tsp`.
            - `Budget` - `Mapping`. Describes, when to terminate one task execution.
                - `Type` - `string`. Type of termination criteria. Supported: `StoppingByTime`.
                - `Amount` - `number`. Amount of budget, given for optimization. If Time-based budget is used, amount is specified in seconds.
            - `Hyperparameters` - `string`. Specifies, which parameters of meta-heuristics to use. 
            Available choices: `default` and `tuned` forces each run to use static meta-heuristic parameters, default and tuned in offline respectively.
            Any other value of `Hyperparameters` implies the use of provided by `main-node` meta-heuristic parameters.  
    - `Objectives` - `List of strings`. A list of metrics that the target system reports back.
    - `ObjectivesDataTypes` - `List of strings`. Python data types of the target system output metrics.
    - `ObjectivesMinimization` - `List of booleans`. Which reported metrics are minimized.
    - `ObjectivesPriorities` - `List of integers`. Which reported metrics to use for controlling the optimization process (compare configurations).
    - `ObjectivesPrioritiesModels` - `List of integers`. Priorities for the reported metrics to be used for surrogate model creation and optimization.
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
    "NumberOfWorkers": 3,
    "EventService": {
      "Address": "localhost",
      "AMQTPort": 49153,
      "GUIPort": 49154
    },
    "Database": {
      "Address": "172.22.1.167",
      "Port": 27017,
      "DatabaseName": "BRISE_db",
      "DatabaseUser": "BRISEdbuser",
      "DatabasePass": "5V5Scp1E2"
    },
    "COMMENT": "These configurations should also be moved to \"Main node\".",
    "results_storage": "./Results/"
  },
  "SelectionAlgorithm": "MersenneTwister",
  "OutliersDetection":{
    "isEnabled": true,
    "Detectors": [
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
      },
      {
        "Type": "Mad",
        "Parameters": {
          "MinActiveNumberOfTasks": 3,
          "MaxActiveNumberOfTasks": 10000
        }
      },
      {
        "Type": "Grubbs",
        "Parameters": {
          "MinActiveNumberOfTasks": 3,
          "MaxActiveNumberOfTasks": 10000
        }
      },
      {
        "Type": "Quartiles",
        "Parameters": {
          "MinActiveNumberOfTasks": 3,
          "MaxActiveNumberOfTasks": 10000
        }
      }
    ]
  },
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
      "ExperimentAwareness": {
        "isEnabled": true,
        "MaxAcceptableErrors": [50],
        "RatiosMax": [10]
      }
    }
  },
  "Predictor":{
    "window size": 1.0,
    "models": [
      {
        "Type": "brise.TreeParzenEstimator",
        "Parameters": {
          "top_n_percent": 30,
          "random_fraction": 0,
          "bandwidth_factor": 3,
          "min_bandwidth": 0.001,
          "SamplingSize": 96
        }
      }
    ]
  },
  "StopConditionTriggerLogic":{
    "Expression": "(QuantityBased and Guaranteed and ImprovementBased) or BadConfigurationBased or TimeBased",
    "InspectionParameters":{
      "RepetitionPeriod": 1,
      "TimeUnit": "seconds"
    }
  },
  "StopCondition":[
    {
      "Name": "QuantityBased",
      "Type": "QuantityBased",
      "Parameters": {
        "MaxConfigs": 15
      }
    },
    {
      "Name": "ImprovementBased",
      "Type": "ImprovementBased",
      "Parameters": {
        "MaxConfigsWithoutImprovement": 5
      }
    },
    {
      "Name": "Guaranteed",
      "Type": "Guaranteed",
      "Parameters": {      }
    },
    {
      "Name": "BadConfigurationBased",
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
      }
    },
    {
      "Name": "TimeBased",
      "Type": "TimeBased",
      "Parameters": {
        "MaxRunTime": 10,
        "TimeUnit": "minutes"
      }
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
    "DataFile"          : "./Resources/EnergyExperimentData.json"
  },
  "TaskConfiguration":{
    "TaskName"          : "energy_consumption",
    "Scenario":{
      "ws_file": "Radix-500mio.csv"
    },
    "Objectives"   : ["energy"],
    "ObjectivesDataTypes"  : ["float"],
    "ObjectivesMinimization": [true],
    "ObjectivesPriorities": [1],
    "ObjectivesPrioritiesModels": [1],
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
  "name": "experiment",
  "type": "NominalHyperparameter",
  "categories": [
    {
      "category": "SynteticProblems",
      "children": [
        {
          "name": "x",
          "type": "FloatHyperparameter",
          "lower": -4.0,
          "upper": 5.0,
          "default": 1
        },
         {
          "name": "y",
          "type": "FloatHyperparameter",
          "lower": -4.0,
          "upper": 5.0,
          "default": 1
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
