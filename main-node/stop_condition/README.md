# Stop Condition.
##### This folder contains a Basic Stop Condition class and different stop condition types, which are implemented as wrappers on the Basic Stop Condition. When you specify a Stop Condition in the Experiment description file `stop_condition_selector.py` reads the description and builds the Stop Condition object.

All Stop Conditions are splitted in 2 groups: posterior and prior. Prior Stop Conditions can be initialized right away after experiment starts, while posterior Stop Conditions require statistical data collected during experiment.

In the current implementation, BRISE will stop if Basic Stop Condition and all additional posterior Stop Conditions agree on stopping BRISE or one of prior Stop Conditions decided to stop BRISE. If at least one of posterior and all of prior conditions were not satisfied BRISE will continue running.

## Variants of stop condition config


#### Basic Stop Condition

This Stop Condition is satisfied, when there is at least 1 successfully measured Configuration. Used as a base for Stop Condition Decorator.

#### Default Stop Condition

This posterior Stop Condition is satisfied, when the number of overall measured Configurations is greater than `StopCondition["MaxConfigs"]`.

```json
"StopCondition":[
    {
      "Type": "Default",
      "Parameters": {
        "MaxConfigs": 15
      }
    }
  ]
```

#### Guaranteed Stop Condition

This posterior Stop Condition is satisfied, when the better Configuration than Default Configuration was found.

```json
"StopCondition":[
    {
      "Type": "Guaranteed",
      "Parameters": {      }
    }
  ]
```

#### Improvement Based Stop Condition

This posterior Stop Condition is satisfied, when the better Configuration was not found after evaluating `StopCondition["MaxConfigsWithoutImprovement"]` number of Configurations in a row.

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

This posterior Stop Condition is satisfied, when the BRISE had evaluated some percentage of overall number of Configurations in the Search Space. 
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

#### Time Based Stop Condition

This prior Stop Condition is satisfied, when the user-defined timeout is reached.
This timeout could be set using `StopCondition["MaxRunTime"]` and `StopCondition["TimeUnit"]` parameters of Time Based Stop Condition that represent time value and time unit (seconds, minutes etc.) respectively.

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

#### Bad Configuration Based Stop Condition

This prior Stop Condition is satisfied, when total number of broken, failed and not suitable Configurations reaches user-defined limit. This limit is reflected as `StopCondition["MaxBadConfigurations"]` parameter for Bad Configuration Based Stop Condition.

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
####And can be used in different combinations

```json
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
```
