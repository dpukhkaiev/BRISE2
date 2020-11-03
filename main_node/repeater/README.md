# Repetition management.
Repetition management (repeater) is a mandatory feature of BRISE which ensures statistical significance of target system evaluations
by the means of performing multiple repetitions for each individual configuration.

This folder contains a basic Repetition management class (`repeater.py`) which is responsible for the communication with Worker Service;
and its concrete variants, which represent different repetition management strategies. Moreover, it contains 
a `repeater_selector.py` file, which instantiates the exact repetition management strategy based on
user preferences from `SettingBRISE.json` file.
  
Each repetition management strategy should contain `MaxFailedTasksPerConfiguration` parameter, which specifies a 
threshold, exceeding which the configuration is considered to be broken and no further evaluations will be conducted, 
i.e., `"MaxFailedTasksPerConfiguration": 5` implies that after "> 5" tasks with invalid or unexpected results its 
evaluation is stopped preemptively. 
 
In its current implementation two strategies are available:
 
 ## Quantity-based repetition management
 This strategy repeats each configuration *exactly* `MaxTasksPerConfiguration` times.
 
 ```json
  "Repeater":{
    "Type": "QuantityBased",
    "Parameters": {
      "MaxTasksPerConfiguration": 10,
      "MaxFailedTasksPerConfiguration": 5
    }
  }
```
 
 ## Acceptable-error-based repetition management
 This strategy is inspired by the notion of an acceptable measurement error, which can be specified by the user 
 with `BaseAcceptableErrors`  field. This parameter denotes a maximal relative fluctuation of a result a configuration 
 is allowed to have. Repetitions continue to be performed unless the mean of Task results is less than `BaseAcceptableErrors`
 or `MaxTasksPerConfiguration` threshold is reached.
 
 * `MinTasksPerConfiguration` is a minimal number of evaluations performed for each configuration, in case of the current 
 strategy its minimum value equals 2 to calculate the relative error.
 * `ConfidenceLevels` is a probability according which the result of the evaluation resides within boundaries derived from 
 `BaseAcceptableErrors`.
 
 The following two parameters are related to a relative error of a single configuration evaluation. 
 * `DevicesScaleAccuracies` is a number of digits after a decimal point.
 * `DevicesAccuracyClasses` denote an accuracy class of the "device" that evaluates the objective function. More informantion 
 can be found [here](https://en.wikipedia.org/wiki/Class_of_accuracy_in_electrical_measurements). 
 
 `Please, leave both parameters as 0 if unsure. In this case it is assumed that there is no error in the single evaluation.`
 
 Note, that `BaseAcceptableErrors`, `ConfidenceLevels`, `DevicesScaleAccuracies` and `DevicesAccuracyClasses` are lists 
 as these parameters should be specified for each objective separately in a multi-objective scenario.
   
 ```json
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
        "isEnabled": false,
      }
    }
  }
```

 ### Experiment-aware acceptable-error-based repetition management
 An enhancement of acceptable-error-based strategy that utilizes a runtime knowledge on the best configuration obtained 
 so far to decrease the number of repetitions in unpromising areas of the search space. If enabled, this strategy
 relaxes Task result's preciseness requirements from `BaseAcceptableErrors` to `MaxAcceptableErrors` for configurations
  that are `RatiosMax` times worse than the best configuration obtained so far.
  
  `NOTE: MinTasksPerConfiguration is applied to promising configurations only, unpromising configurations can be 
  stopped after a single measurement.`
   
 ```json
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
  }
```

##### To get more information on ranges of parameters, please consult with [repeater schema](./schema/repeater.schema.json)

 ## Extension 
 To add your own repetition management strategy, create a separate python-file in this folder with a class that 
 extends `Repeater` class and implement `evaluate(...)` method. The new strategy won't go through the validation process 
 until you add an entry for it in [repeater schema](./schema/repeater.schema.json) and register it in 
 [experiment schema](./../Resources/schema/experiment.schema.json)