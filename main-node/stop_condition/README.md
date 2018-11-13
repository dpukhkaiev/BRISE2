# Stop Condition.
###### This folder contains abstract class and different stop condition implementations.

## Variants of stop condition config
###### Stop condition config depends on the stop condition type

#### Adaptive Stop Condition

```json
"StopCondition": { 
   "adaptive": { 
       "SearchSpacePercentageWithoutImprovement": 10
   }
}
```

#### Default Stop Condition

```json
"StopCondition": { 
   "default": { 
       "MaxConfigsWithoutImprovement": 3
   }
}
```

#### Improvement Based Stop Condition

```json
"StopCondition": { 
   "improvement_based": { 
       "MaxConfigsWithoutImprovement": 3
   }
}
```
