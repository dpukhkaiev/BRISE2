# Stop Condition.
###### This folder contains abstract class and different stop condition implementations.

## Variants of stop condition config
###### Stop condition config depends on the stop condition type

#### Adaptive Stop Condition

The Solution finding stops if the solution candidate's value is not improved more, then `N` times successively. `N` is calculated as part of full search space size. The part is determined by configs's value - `SearchSpacePercentageWithoutImprovement`.

```json
"StopCondition": { 
   "adaptive": { 
       "SearchSpacePercentageWithoutImprovement": 10
   }
}
```

#### Default Stop Condition

The Solution finding stops if the solution candidate's value is not improved more, then `stop_condition_type["MaxConfigsWithoutImprovement"]` times successively.

```json
"StopCondition": { 
   "default": { 
       "MaxConfigsWithoutImprovement": 3
   }
}
```

#### Improvement Based Stop Condition

The Solution finding stops if the solution candidate's value is not improved more, then `stop_condition_type["MaxConfigsWithoutImprovement"]` times successively and is better, then the value of default point.

```json
"StopCondition": { 
   "improvement_based": { 
       "MaxConfigsWithoutImprovement": 3
   }
}
```
