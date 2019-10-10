## BRISE configuration files
###### This folder contains examples of *json* configuration files.

### The configuration files entities explanation
Process of finding (near)optimal configuration of target system should be described in 4 general topics (top-level-keys in json file) of the configuration file.
All other configurations are nested to these as key-value entities.

Possible values of configurations for your system should be provided in separate json file.

**All specified here configurations are required.**

- `General` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `isMinimizationExperiment` - `bool`. Minimization or maximization experiment
    - `ConfigurationsPerIteration` - `int`. The number of configurations that will be measured simultaneously. **optional**

- `DomainDescription` - describes what configurations the target system uses. Value - `dictionary` with following key-value pairs.
    - `FeatureNames` - `list of strings`. The names of configurations.
    - `DataFile` - `string`. Path to json file with all possible values of all configurations. 
    - `AllConfigurations` - here will be loaded configurations from the `DataFile`.
    - `DefaultConfiguration` - `list of values`. **an order must match the `FeatureNames`**. User`s assumption about a default configuration that system uses.

- `SelectionAlgorithm` - describes the way of search space (all possible configuration) exploration.
    - `SelectionType` - `string`. An exploration algorithm specification. Currently only `SobolSequence` available.
    - `NumberOfInitialConfigurations` - `int`. The number of configurations that will be tested before making any attempts to build prediction model.

- `TaskConfiguration` - this section describes general configuration for Worker Service and your system during testing.
    - `TaskName` - `string`. The Worker nodes are able to run different experiments/tasks. This value identifies needed.
    - `Scenario` - `dict`. the experiments/tasks configuration that is static and is needed to be passed to Worker nodes each time.
    - `TaskParamenters` - `List of strings`. Configurations that the Worker nodes will use to run target system.
    - `ResultStructure` - `List of strings`. Configurations that the Worker nodes will report back to Main node. `TaskParameters` should be included. 
    - `ResultDataTypes` - `List of strings`. Should be a proper names of Python data types, used for casting data that arrives from Worker nodes (as strings).
    - `MaxTimeToRunTask` - `float`. Maximum time to run each task in seconds. In case of exceeding the task will be terminated.

- `OutliersDetection` - the results of each Configuration run (Tasks) could differ significantly from other observations (Tasks) and those bias Configuration measurement results.
    This module could find these Tasks and exclude them from the Configuration results.
    *Note that appearance of new Tasks could change the decision made before.*

    The parameters for OutliersDetection module appear as a list of dictionaries, each of them contains two required key-value pairs:
    - `Type` - `string` - the name of Outlier Detection criterion (a.k.a. test or detector). Variants: `Dixon`, `Chauvenet`, `MAD`, `Grubbs`, `Quartiles`.
    - `Parameters` - `dictionary` - a set of key-value parameters used by specified in `Type` criterion.

    Current implementation of OutlierDetection module supports 5 detectors to distinguish whether the Task is Outlier or not.
    - `Dixon` - Dixon test calculates distance between suspicious value and closest one to it, then received value is divided on distance between min and max value in sample and checks this value in coefficient table.
    - `Chauvenet` - The idea behind Chauvenet's criterion is to find a probability band, centered on the mean of a normal distribution, that should reasonably contain all n samples of a data set.
    - `MAD` - It is the median of the set comprising the absolute values of the differences between the median and each data point.
    - `Grubbs` - The test finds if a minimum value or a maximum value is an outlier.
    - `Quartiles` - This test splits data into quartiles, then finds interquartile distance. All values, that goes beyond (Q1-3*IQR : Q3+3*IQR) are outliers.

    Each of described above criteria could be enabled by including it to the Experiment Description with two required parameters:
    - `MinActiveNumberOfTasks` - `int` - a minimum number of Tasks in Configuration to enable criterion.
    - `MaxActiveNumberOfTasks` - `int` - a maximum number of Tasks in Configuration while the criterion still works. In case of exceeding this boundary, the criterion will be disabled. The string value `"Inf"` is supported.

    This was done while each test is suitable for different amount and structure of available data.
    In case of enabling several criteria, the Task will be marked as *Outlier* if at least half of tests mark the Task as *Outlier*.

- `RepeaterConfiguration` - Results of each Configuration evaluation could not be precise/deterministic. The intent of Repeater is to reduce the variance between the evaluation of each Configuration by running it several times (Tasks).
    - `Type` - `string` - a type of repeater represents a strategy to check the accuracy of the Configuration measurement. Variants: `default`, `student_deviation`
        - `default` - evaluates Configuration *MaxTasksPerConfiguration* times. Required parameters:
            - `MaxTasksPerConfiguration` - a maximum number of times to evaluate (run) each Configuration.
        - `student_deviation` - checks the overall absolute deviation between Tasks and takes into account the Configuration quality (how close it is to the currently best Configuration found). Required parameters:
            - `MinTasksPerConfiguration` - `int` - a minimum number of repetitions to evaluate (run) each Configuration.
            - `MaxTasksPerConfiguration` - `int` - a maximum number of repetitions to evaluate (run) each Configuration. After reaching this amount new Tasks will not be added to the Configuration.
            - `BaseAcceptableErrors` - `array of floating numbers` - A starting value for an acceptable Relative Error for each dimension in result.
            - `ConfidenceLevels` - `array of floating numbers 0..1` - Probabilities, that Configuration results (each dimension) will appear in a boundary of an Acceptable Relative error.
            - `DevicesScaleAccuracies` - `array of floating numbers` - A minimal value on a device scale, that is possible to distinguish for each dimension in results.
            - `DevicesAccuracyClasses` - `array of integers` - Accuracy classes of devices that is used to estimate each dimension of the result.
            - `ModelAware` - `boolean` - Is Repeater is in model-aware mode? If yes (`true`), the following parameters are obligatory:
                - `MaxAcceptableErrors` - `array of floating numbers` - A maximal value for the Acceptable Relative errors, used if the Repeater is model-aware.
                - `RatioMax` - `array of floating numbers` - A relation between current solution Configuration and current Configuration, when Relative error threshold will reach MaxAcceptableErrors value. Specified separately for each dimension in a results.
            
    - *To disable repeater* (if the target algorithm is deterministic or Configuration evaluation considered precise) set `MaxTasksPerConfiguration` equal to `1` and `Type` to `default`.
 
     
- `ModelConfiguration` - section with the configuration related to the prediction model creating process.
    - `minimalTestingSize` - `float`. A minimum possible fraction that specifies an amount of data for testing the created prediction model.
    - `maximalTestingSize` - `float`. A fraction that specifies an amount of data for testing the created prediction model.
    - `MinimumAccuracy` - `float`. A minimum accuracy that model should provide before making any predictions/testing.
    - `ModelType` - `string`. Type of heuristic prediction model. *Variants:* 
        - `regression` - Polynomial regression model.
        - `BO` - Bayesian Optimization model (using the Tree Parzen Estimator or TPE).

- `StopCondition` - when to stop BRISE.
    - `Stop Condition Name` - `String` Strategy used for BRISE termination. *Variants (with parameters)*
        - `default` - `String`(key, value - parameters for Stop Condition (as a nested dictionary)) - The BRISE will stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - ? (need to refine this description).
        - `improvement_based` - `String` - The BRISE could (but don't have to) stop in case of founding Configuration better, than Default configuration.
            `MaxConfigsWithoutImprovement` - `Int` - Terminate after this amount of Configurations were tested and no better found. (but still, better than default was found).
        - `adaptive` - `String`- Stop if no improvement got for current solution after some percentage of overall Configuration search space evaluation.
            - `SearchSpacePercentageWithoutImprovement` - `Int` - % of the Configuration search space evaluated without improvement.
        - `TimeBased` - `String` - Launches user-defined timer. The BRISE will stop when time is over.
        Required parameters:
            - `MaxRunTime` - `Int` - Time value for timer.
            - `TimeUnit` - `String` - Time unit for timer (seconds, minutes etc).
        - `BadConfigurationBased` - `String` - The BRISE will stop in case of reaching threshold of failed Configurations number.
        Required parameters:
            - `MaxBadConfigurations` - `Int` - Threshold of failed Configurations. Failed configuration should not contain any correct measurings.

#### We provide validation of the Experiment Description file using JSON-Schema.
* The project JSON-Schema could be found [here](./schema/experiment.schema.json).
* An example of valid Experiment Description file could be found [here](./EnergyExperiment.json).
* The related Domain Description Data file could be found [here](./EnergyExperimentData.json).

##### Links to investigate JSON-Schema:
* For validation JSON documents use [json-schema.org](https://json-schema.org/)
* Useful examples are in [understanding-json-schema](https://json-schema.org/understanding-json-schema/index.html) section.
