# Repetition management.
Repetition management is a mandatory feature of BRISE which ensures statistical significance of target system evaluations
by the means of performing multiple repetitions for each individual configuration.

This folder contains a basic Repetition management class [repeater.py](repeater.py) which is responsible for the communication with workers;
and its concrete variants, which represent different repetition management strategies. Moreover, it contains 
a [repeater_selector.py](repeater_selector.py) file, which instantiates the exact repetition management strategy based
on product configuration.
  
Each repetition management strategy contains `MaxFailedTasksPerConfiguration` parameter, which specifies a 
threshold, exceeding which the configuration is considered to be broken and no further evaluations will be conducted, 
i.e., `MaxFailedTasksPerConfiguration = 5` implies that after "> 5" tasks with invalid or unexpected results its 
evaluation is stopped preemptively.

The feature model of RepetitionManager looks as follows:
 ```json
RepetitionManager {
  MaxFailedTasksPerConfiguration -> integer
  [MaxFailedTasksPerConfiguration >= 1]

  xor Instance {
    QuantityBased {
      MaxTasksPerConfiguration -> integer
      [MaxTasksPerConfiguration >= 1]

      Type -> predefined
      [Type = "quantity_based"]
    }
    AcceptableErrorBased {
      MinTasksPerConfiguration -> integer
      MaxTasksPerConfiguration -> integer
      [MinTasksPerConfiguration >= 2]
      [MinTasksPerConfiguration <= MaxTasksPerConfiguration]

      BaseAcceptableError -> float
      [BaseAcceptableError > 0]
      [BaseAcceptableError < 100]

      ConfidenceLevel -> float
      [ConfidenceLevel > 0]
      [ConfidenceLevel <= 1]

      Type -> predefined
      [Type = "acceptable_error_based"]

      ExperimentAware ? {
        MaxAcceptableError -> float
        [MaxAcceptableError > parent.BaseAcceptableError]
        [MaxAcceptableError < 100]

        RatioMax -> float
        [RatioMax > 0]

        MinTasksPerUnderperformingConfiguration -> predefined
        [MinTasksPerUnderperformingConfiguration = 1]
      }
    }
  }

```
 
In its current implementation two strategies are available:
 
 ## Quantity-based repetition management
 This strategy repeats each configuration *exactly* `MaxTasksPerConfiguration` times.
  
 ## Acceptable-error-based repetition management
 This strategy is inspired by the notion of an acceptable measurement error, which can be specified by the user 
 with `BaseAcceptableError`  field. This parameter denotes a maximal relative fluctuation of a result a configuration 
 is allowed to have. Repetitions continue to be performed unless the mean of Task results is less than `BaseAcceptableError`
 or `MaxTasksPerConfiguration` threshold is reached.
 
 * `MinTasksPerConfiguration` is a minimal number of evaluations performed for each configuration, in case of the current 
 strategy its minimum value equals 2 to calculate the relative error.
 * `ConfidenceLevel` is a probability according which the result of the evaluation resides within boundaries derived from 
 `BaseAcceptableError`.

 ### Experiment-aware acceptable-error-based repetition management
 An enhancement of acceptable-error-based strategy that utilizes runtime knowledge on the best configuration obtained 
 so far to decrease the number of repetitions in unpromising areas of the search space. If enabled, this strategy
 relaxes Task result's preciseness requirements from `BaseAcceptableError` to `MaxAcceptableError` for configurations
  that are `RatioMax` times worse than the best configuration obtained so far.
  
  `NOTE: MinTasksPerConfiguration is applied to promising configurations only, unpromising configurations can be 
  stopped after a single measurement.`

 ## Extension 
 To add your own repetition management strategy, create a separate python-file in this folder with a class that 
 extends `Repeater` class and implements `evaluate(...)` method. The new strategy won't be available within the SPL until
 it is added into the feature model.