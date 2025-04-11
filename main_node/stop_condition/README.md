# Stop Condition.

When you select a Stop Condition during product configuration process [stop_condition_selector.py](stop_condition_selector.py) reads the resulting `Json-file`
 and builds Stop Condition modules. 

Each Stop Condition periodically performs self-validation according to a user-defined repetition 
interval. Stop Condition Validator orchestrates all Stop Conditions. Connection between them is implemented through events. 

The user could specify any logic of BRISE Experiment termination by composing operands `and`, `or`, brackets `(` `)` 
and names of Stop Conditions into a single expression.
This expression should be specified within `Expression` attribute of `StopConditionTriggerLogic` feature.

**Note: Stop Conditions, that are selected within `StopCondition` feature, but not used in `StopConditionTriggerLogic` are ignored.**

```json
StopCondition {
  Instance {
    ...
  }
  StopConditionTriggerLogic {
    Expression -> string
    InspectionParameters {
      RepetitionPeriod -> integer
      TimeUnit -> string
      [RepetitionPeriod > 0]
      [TimeUnit in {"seconds", "minutes", "hours", "days"}]
    }
  }
}
```

Example of a `StopConditionTriggerLogic` expression:

`(QuantityBased and Guaranteed and ImprovementBased and Adaptive) or BadConfigurationBased`,
where each element is contained within `Name` attribute of a `StopCondition` instance.

## Feature model
Feature model allows selecting unspecified number of each stop condition under condition that all `Name` values are unique.
 `FewShotLearningBasedSC` is enabled via a cross-tree constraint from the [Transfer learning](../transfer_learning) component.
```json
abstract SC {
  Type -> predefined
  Name -> string
}
StopCondition {
  Instance {
    AdaptiveSC : SC * {
      Parameters {
        SearchSpacePercentage -> float
        [SearchSpacePercentage > 0]
        [SearchSpacePercentage < 100]
      }
      [Type = "adaptive"]
    }
    BadConfigurationBasedSC : SC *{
      Parameters {
        MaxBadConfigurations -> integer
        [MaxBadConfigurations > 0]
      }
      [Type = "bad_configuration_based"]
    }
    FewShotLearningBasedSC : SC 0 {
      [Type = "few_shot_learning_based"]
    }
    GuaranteedSC : SC * {
      [Type = "guaranteed"]
    }
    ImprovementBasedSC : SC * {
      Parameters {
        MaxConfigsWithoutImprovement -> integer
        [MaxConfigsWithoutImprovement > 0]
      }
      [Type = "improvement_based"]
    }
    QuantityBasedSC : SC * {
      Parameters {
        MaxConfigs -> integer
        [MaxConfigs > 0]
      }
      [Type = "quantity_based"]
    }
    TimeBasedSC : SC * {
      Parameters {
        MaxRunTime -> integer
        TimeUnit -> string
        [MaxRunTime > 0]
        [TimeUnit in {"seconds", "minutes", "hours", "days"}]
      }
      [Type = "time_based"]
    }
    ValidationBasedSC : SC * {
        [Type = "validation_based"]
    }
    [size childs.self > 0]
    [size unique Name at self == size childs.self]
  }
  StopConditionTriggerLogic {
    Expression -> string
    InspectionParameters {
      RepetitionPeriod -> integer
      TimeUnit -> string
      [RepetitionPeriod > 0]
      [TimeUnit in {"seconds", "minutes", "hours", "days"}]
    }
  }
}
```
## Variants of Stop Condition

#### Quantity Based Stop Condition

This Stop Condition is satisfied, when the number of overall measured Configurations is greater than `MaxConfigs`.


#### Guaranteed Stop Condition

This Stop Condition is satisfied, when a better Configuration than the Default Configuration was found.


#### Improvement Based Stop Condition

This Stop Condition is satisfied, when a better Configuration was not found after evaluating 
`MaxConfigsWithoutImprovement` number of Configurations in a row.

#### Adaptive Stop Condition

This Stop Condition is satisfied, when the BRISE had evaluated some percentage of overall number of Configurations in the Search Space. 
This percentage can be specified by `SearchSpacePercentage` parameter for Adaptive Stop Condition.

#### Bad Configuration Based Stop Condition

This Stop Condition is satisfied, when a total number of broken, failed or not suitable Configurations reaches a 
user-defined limit. This limit is reflected as `MaxBadConfigurations` parameter for Bad Configuration 
Based Stop Condition.


#### Time Based Stop Condition

This Stop Condition terminates BRISE execution, when the user-defined timeout is reached.
This timeout could be set using `MaxRunTime` and `TimeUnit` parameters 
that represent time value and time unit (seconds, minutes or hours) respectively.


#### Validation Based Stop Condition

This Stop Condition is satisfied, when the model created during BRISE run is valid.

#### Few-shot-learning Based Stop Condition

This Stop Condition is fired, when at least one entity was transferred to the current experiment via the transfer learning module.
