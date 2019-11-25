# Stop Condition.
##### This folder contains a Basic Stop Condition class and different stop condition types, which are implemented as wrappers on the Basic Stop Condition. When you specify a Stop Condition in the Experiment description file `stop_condition_selector.py` reads the description and builds the Stop Condition object.
In the current implementation, BRISE will stop if Basic Stop Condition and all wrappers (additional Stop Conditions) agree on stopping BRISE. Even if one of all conditions was not satisfied BRISE will continue running.

## Variants of stop condition config


#### Basic Stop Condition

This Stop Condition is satisfied, when the number of overall measured Configurations is greater than 0. Used as a base for Stop Condition Decorator.

#### Default Stop Condition

This Stop Condition is satisfied, when the number of overall measured Configurations is greater than `StopCondition["MaxConfigs"]`.

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
      "Parameters": {}
    },
    {
      "Type": "Adaptive",
      "Parameters": {
        "SearchSpacePercentage": 15
      }
    }
  ]
```