# Stop Condition.
##### This folder contains an Abstract Stop Condition class and some available out of the box Stop Conditions.

When you specify a Stop Condition in the Experiment description file `stop_condition_selector.py` reads the description and builds Stop Condition modules. 

Each Stop Condition (except TimeBased) perform self-validation periodically according to user-defined repetition interval. Stop Condition Validator orchestrates all Stop Conditions. Connection between them implemented through events. 

The user could specify any logic of BRISE Experiment termination by composing operands `and`, `or`, brackets `(` `)` and names of Stop Conditions into single expression.
This expression should be written at `StopConditionTriggerLogic` field of a BRISE settings file.
###### Note: Stop Conditions, that are defined in `StopCondition` block, but not used in `StopConditionTriggerLogic` block will be ignored.
Example of `StopConditionTriggerLogic` field:

```json
"StopConditionTriggerLogic":{
    "Expression": "(QuantityBased and Guaranteed and ImprovementBased and Adaptive) or BadConfigurationBased",
    "InspectionParameters":{
      "RepetitionPeriod": 10,
      "TimeUnit": "seconds"
    }
}
```

## Variants of Stop Condition configurations

#### Quantity Based Stop Condition

This Stop Condition is satisfied, when the number of overall measured Configurations is greater than `StopCondition["MaxConfigs"]`.

```json
"StopCondition":[
    {
      "Type": "QuantityBased",
      "Parameters": {
        "MaxConfigs": 15
      }
    }
  ]
```

#### Guaranteed Stop Condition

This Stop Condition is satisfied, when the better Configuration than Default Configuration was found.

```json
"StopCondition":[
    {
      "Type": "Guaranteed",
      "Parameters": {      }
    }
  ]
```

#### Improvement Based Stop Condition

This Stop Condition is satisfied, when the better Configuration was not found after evaluating `StopCondition["MaxConfigsWithoutImprovement"]` number of Configurations in a row.

```json
"StopCondition":[
    {
      "Type": "ImprovementBased",
      "Parameters": {
        "MaxConfigsWithoutImprovement": 5
      }
    }
  ]
```

#### Adaptive Stop Condition

This Stop Condition is satisfied, when the BRISE had evaluated some percentage of overall number of Configurations in the Search Space. 
This percentage is reflected as `StopCondition["SearchSpacePercentage"]` parameter for Adaptive Stop Condition.

```json
"StopCondition":[
    {
      "Type": "Adaptive",
      "Parameters": {
        "SearchSpacePercentage": 15
      }
    }
  ]
```
#### Bad Configuration Based Stop Condition

This Stop Condition is satisfied, when total number of broken, failed and not suitable Configurations reaches user-defined limit. This limit is reflected as `StopCondition["MaxBadConfigurations"]` parameter for Bad Configuration Based Stop Condition.

```json
"StopCondition":[
    {
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
      }
    }
  ]
```

#### Time Based Stop Condition

This Stop Condition terminates BRISE execution, when the user-defined timeout is reached.
This timeout could be set using `StopCondition["MaxRunTime"]` and `StopCondition["TimeUnit"]` parameters that represent time value and time unit (seconds, minutes etc.) respectively.

```json
"StopCondition":[
    {
      "Type": "TimeBased",
      "Parameters": {
        "MaxRunTime": 10,
        "TimeUnit": "minutes"
      }
    }
  ]
```

#### Validation Based Stop Condition

This Stop Condition is satisfied, when the model created during BRISE runtime is valid.

```json
"StopCondition":[
    {
      "Type": "ValidationBased",
      "Parameters": {      }
    }
  ]
```

#### An example of Stop Condition modules settings:

```json
"StopConditionTriggerLogic":{
    "Expression": "(QuantityBased and Guaranteed and ImprovementBased and Adaptive or ValidationBased) or BadConfigurationBased",
    "InspectionParameters":{
      "RepetitionPeriod": 10,
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
      "Type": "Adaptive",
      "Parameters": {
        "SearchSpacePercentage": 15
      }
    },
    {
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
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
      "Type": "ValidationBased",
      "Parameters": {      }
    }
  ]
```
