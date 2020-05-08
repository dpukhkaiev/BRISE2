# Stop Condition.
##### This folder contains an Abstract Stop Condition class and some available out of the box Stop Conditions.

When you specify a Stop Condition in the Experiment description file `stop_condition_selector.py` reads the description
 and builds Stop Condition modules. 

Each Stop Condition periodically performs self-validation according to a user-defined repetition 
interval. Stop Condition Validator orchestrates all Stop Conditions. Connection between them is implemented through events. 

The user could specify any logic of BRISE Experiment termination by composing operands `and`, `or`, brackets `(` `)` 
and names of Stop Conditions into a single expression.
This expression should be written at `StopConditionTriggerLogic` block of a BRISE settings file.
###### Note: Stop Conditions, that are defined in `StopCondition` block, but not used in `StopConditionTriggerLogic` block will be ignored.
Example of `StopConditionTriggerLogic` block:

```json
"StopConditionTriggerLogic":{
    "Expression": "(QuantityBased and Guaranteed and ImprovementBased and Adaptive) or BadConfigurationBased",
    "InspectionParameters":{
      "RepetitionPeriod": 10,
      "TimeUnit": "seconds"
    }
}
```
## Stop Condition "Name" and "Type" parameters

#### Name

"Name" reflects Stop Condition ID. Each name should be unique. You could use any combination of letters, numericals and special symbols to define name. 

##### Hint: Use meaningful name which consists of Stop Condition type and Stop Condition parameters.
For example "Name": "TimeBased10m" which reflects "TimeBased" Stop Condition with 10 minutes timeout.

#### Type

"Type" reflects BRISE Experiment termination strategy with own parameter set. Each type is designed to spot different trigger events. You could use only predefined set of types. Any other type will cause an error, and the experiment will be terminated.
All Stop Condition types are described in the section below.

## Variants of Stop Condition configurations

#### Quantity Based Stop Condition

This Stop Condition is satisfied, when the number of overall measured Configurations is greater than `StopCondition["MaxConfigs"]`.

```json
"StopCondition":[
    {
      "Name": "QuantityBased",
      "Type": "QuantityBased",
      "Parameters": {
        "MaxConfigs": 15
      }
    }
  ]
```

#### Guaranteed Stop Condition

This Stop Condition is satisfied, when a better Configuration than the Default Configuration was found.

```json
"StopCondition":[
    {
      "Name": "Guaranteed",
      "Type": "Guaranteed",
      "Parameters": {      }
    }
  ]
```

#### Improvement Based Stop Condition

This Stop Condition is satisfied, when a better Configuration was not found after evaluating 
`StopCondition["MaxConfigsWithoutImprovement"]` number of Configurations in a row.

```json
"StopCondition":[
    {
      "Name": "ImprovementBased",
      "Type": "ImprovementBased",
      "Parameters": {
        "MaxConfigsWithoutImprovement": 5
      }
    }
  ]
```

#### Adaptive Stop Condition

This Stop Condition is satisfied, when the BRISE had evaluated some percentage of overall number of Configurations in the Search Space. 
This percentage can be specified by `StopCondition["SearchSpacePercentage"]` parameter for Adaptive Stop Condition.

```json
"StopCondition":[
    {
      "Name": "Adaptive",
      "Type": "Adaptive",
      "Parameters": {
        "SearchSpacePercentage": 15
      }
    }
  ]
```
#### Bad Configuration Based Stop Condition

This Stop Condition is satisfied, when a total number of broken, failed or not suitable Configurations reaches a 
user-defined limit. This limit is reflected as `StopCondition["MaxBadConfigurations"]` parameter for Bad Configuration 
Based Stop Condition.

```json
"StopCondition":[
    {
      "Name": "BadConfigurationBased",
      "Type": "BadConfigurationBased",
      "Parameters": {
        "MaxBadConfigurations": 10
      }
    }
  ]
```

#### Time Based Stop Condition

This Stop Condition terminates BRISE execution, when the user-defined timeout is reached.
This timeout could be set using `StopCondition["MaxRunTime"]` and `StopCondition["TimeUnit"]` parameters 
that represent time value and time unit (seconds, minutes, etc.) respectively.

```json
"StopCondition":[
    {
      "Name": "TimeBased",
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
      "Name": "ValidationBased",
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
      "Name": "Adaptive",
      "Type": "Adaptive",
      "Parameters": {
        "SearchSpacePercentage": 15
      }
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
    },
    {
      "Name": "ValidationBased",
      "Type": "ValidationBased",
      "Parameters": {      }
    }
  ]
```
