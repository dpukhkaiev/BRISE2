# BRISE variability model and configuration files
This directory contains examples of *wfl* feature models and resulting *json* configuration files.
In this document, we use the [base variability model](tests/waffle_models/base.wfl) as the running example.
## BRISE feature model

The variability model of BRISE comprise two main building blocks:
1. [Context model](tests/waffle_models/base.wfl#L61), specifying characteristics of the optimization problem at hand.
2. [Feature model](tests/waffle_models/base.wfl#L109), capturing all variability points of the SPL.

Unless extending the framework with novel mechanisms, the feature model must be left intact. 
The context model, in turn, must be adjusted for each experiment.

### Context model
Our exemplary context model comprises two sub-features: [`TaskConfiguration`](tests/waffle_models/base.wfl#L63) and [`SearchSpace`](tests/waffle_models/base.wfl#L97). 

#### Task Configuration:
Which contains: 
  * `TaskName` that is utilized to find the corresponding worker-method. 
In our example, `TaskName` = "test", resulting in identification of the following [worker method](../../worker/worker.py#L4) 
  * `MaxTimeToRunTask` is the maximal execution time allowed for a single evaluation. 
If the worker exceeds this time cap, the configuration is dropped and is considered as broken. 
  * `Scenario` data, which is used to identify a concrete optimization problem within a set of similar problems. 
In our example `Scenario` is empty, since testing method is extremely simple. 
An extended `Scenario` feature can be found in the case study of [multi-objective optimization benchmarks](moo_benchmarks/moo_benchmarks.wfl#L70).
  *  `Objective function` data such as:  a name, a data type and a type of optimization activity~(minimization or maximization). 
Moreover, each objective function should possess expected boundaries, which specify the typical return values of the evaluation. 
In case the evaluation returns a value outside of this region, it is considered broken.  

#### Search Space
This feature unites all available parameters, their types and boundaries. 
Moreover, it comprises the `Structure` sub-feature, responsible for modeling dependencies between parameters.

_Flat search space_ creates a single vector for all parameters within the search space, which is then fed into the optimizer.
_Hierarchical search space_ considers dependencies between parameters, creating multiple regions of the search space, each treated by a dedicated optimizer.

### Feature model
BRISE comprises 5 top-level features, responsible for different parts of the optimization process.

#### Configuration Selection 
is a mandatory high-level feature, comprising all surrogate-model-related activities such as: 
surrogate creation, validation and optimization. Moreover, its subfeatures include candidate selection, 
transformation abilities and sampling.

##### Sampling Strategy
component offers an experiment-independent algorithm, which is utilized to select configurations from the search space for a subsequent evaluation. 
The sampling strategy is used when there is no information on the structure of the search space or it is unreliable.
Provided variants are: `SobolSequence`, `MersenneTwister`.

##### Surrogate 
component offers a cheap-to-evaluate approximation of the objective function utilized to decrease the number of evaluated configurations. 
In our framework we provide the following surrogates:
* `Tree-structured Parzen Estimator`, 
* `Fittness-rate-average-based multiarmed bandit`, 
* `Model mock` for surrogate-less approach 
* External models from [scikit-learn-library](https://scikit-learn.org/stable/):
  * [Ordinary least squares Linear Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
  * [Epsilon-Support Vector Regression](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html#sklearn.svm.SVR)
  * [Gradient Boosting for regression](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html)
  * [Bayesian ridge regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.BayesianRidge.html#sklearn.linear_model.BayesianRidge)
  * [Multi-layer Perceptron regressor](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPRegressor.html#sklearn.neural_network.MLPRegressor)
  * [Gaussian process regression](https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html#sklearn.gaussian_process.GaussianProcessRegressor)

##### Optimizer  
component encapsulates an algorithm utilized to optimize the surrogate model. The provided optimizers are:
* `Random Search`, which applies the sampling strategy, specified in the product configuration,
to the surrogate model until the `SamplingSize` budget is depleted.
* `MOEA`, which serves as a wrapper for external  evolutionary algorithms provided by the [pygmo framework for optimization](https://esa.github.io/pygmo2/).
[Supported algorithms](https://esa.github.io/pygmo2/algorithms.html#algorithms-exposed-from-c):
  * Extended Ant Colony Optimization algorithm (gaco), Multi-objective Ant Colony Optimizer (MACO), Grey Wolf Optimizer (gwo), Artificial Bee Colony, Differential Evolution, (N+1)-ES simple evolutionary algorithm, A Simple Genetic Algorithm, Self-adaptive Differential Evolution,Self-adaptive Differential Evolution, pygmo flavour (pDE), Covariance Matrix Evolutionary Strategy,  Multi Objective Evolutionary Algorithms by Decomposition (the DE variant), Particle Swarm Optimization, generational PSO, Non dominated Sorting Particle Swarm Optimization and Non dominated Sorting Genetic Algorithm (NSGA-II).    

##### Validator
The model validation strategy decides whether to use model-based configuration selection or to stick with the sampling plan. Variants:
* `Energy Validator`. This is a custom validation strategy, developed for an empirical study on software energy-efficiency. 
* `Quality Validator` is a generic validation strategy. The main metric of this strategy is the coefficient of determination R^2.
`Quality Validator` can be run in two sub-variants: one-staged or two staged. For details of each variant consult the following publication [1].
* `Mock Validator` can be utilized to disable validation.

[1] Pukhkaiev, D., Husak, O., Götz, S., Aßmann, U. (2021). Multi-objective Parameter Tuning with Dynamic Compositional Surrogate Models. In: Simos, D.E., Pardalos, P.M., Kotsireas, I.S. (eds) Learning and Intelligent Optimization. LION 2021. Lecture Notes in Computer Science(), vol 12931. Springer, Cham. https://doi.org/10.1007/978-3-030-92121-7_26

##### Candidate Selector
component is responsible for picking promising configurations based on the results obtained from the optimizer. Variants:
* `BestMultiPointProposal` selecting best points from the non-dominated front provided by the optimizer.
* `RandomMultiPointProposal` selecting random points from the non-dominated front provided by the optimizer.

**WARNING** in BRISEv2.6.0 only single-point proposal is supported due to architectural restrictions.

##### Configuration Transformer
Configuration transformers are utilized to adapt parameter types to the requirements of the respective entity, which can be either a surrogate model or an optimizer. 

BRISE supports four parameter types. Numerical, which can be 1) integer and 2) float; and categorical: 3) nominal and 4) ordinal.
For each parameter type we offer a dedicated configuration transformer entity: `Integer Transformer`,  `Float Transformer`,  `Nominal Transformer `and  `Ordinal Transformer`.

##### Value Transformer
Value transformers perform adaptation of the objective function  to the requirements of the respective variant. 
We offer two types of value transformation: 
* `Scalarizing` is necessary to handle a multi-objective problem with a single-objective surrogate. 
* `Acquisition Function `is a mandatory part of optimization with Bayesian surrogates, which leverages uncertainty of a probabilistic model to find promising candidates.

#### Repetition management
is a component, responsible for direct handling of non-determinism in optimization problems. For a detailed description of this component consult the respective [documentation page](../../main_node/repeater/README.md)

`OutliersDetection` is an optional feature disabled in BRISE v2.6.0
<details>
The results of each Configuration run (Tasks) could differ significantly 
from other observations (Tasks) and those bias Configuration measurement results.
    This module could find these Tasks and exclude them from the Configuration results.
    *Note, that the evaluation of subsequent Configurations could change the decision made before.*

    Parameters for OutliersDetection module are described by 2 main keys: `bool` variable `isEnabled` (if `true` - OutlierDetection is switched on; if `false` - switched off ) and `Detectors` - a list of dictionaries, each of which contains two required key-value pairs:
    - `Type` - `string` - the name of Outlier Detection criterion (a.k.a. test or detector). Variants: `Dixon`, `Chauvenet`, `MAD`, `Grubbs`, `Quartiles`.
    - `Parameters` - `dictionary` - a set of key-value parameters used by specified in `Type` criterion.

    Current implementation of OutlierDetection module supports 5 detectors to distinguish whether the Task is an outlier or not.
    - `Dixon` - Dixon test calculates the distance between a suspicious value and the closest one to it, then the
     received value is divided by a distance between min and max value in the sample and is checked in coefficient table.
    - `Chauvenet` - The idea behind Chauvenet's criterion is to find a probability band, centered on the mean of a 
    normal distribution, that should reasonably contain all n samples of a data set.
    - `MAD` - It is the median of the set comprising the absolute values of the differences between the median and each data point.
    - `Grubbs` - The test finds if a minimum value or a maximum value is an outlier.
    - `Quartiles` - This test splits data into quartiles, then finds interquartile distance. All values, that goes beyond (Q1-3*IQR : Q3+3*IQR) are outliers.

    Each of the aforementioned criteria could be enabled by including it into the Experiment Description with two required parameters:
    - `MinActiveNumberOfTasks` - `int` - a minimum number of Tasks in Configuration to enable criterion.
    - `MaxActiveNumberOfTasks` - `int` - a maximum number of Tasks in Configuration while the criterion still works. 
    In case of exceeding this boundary, the criterion will be disabled. The string value `"Inf"` is supported.
    
    The reason for specifying the boundaries is in a suitability of each test for different amount and structure of data.
    In case of enabling several criteria, the Task will be marked as *Outlier* if at least a half of tests mark the Task as an *Outlier*.
</details>

#### Stop Condition (SC)
component unites various termination criteria whose role is to determine whether the experiment should be finished. The available variants are:
* Adaptive SC  is satisfied when a specified percentage of the search space has been evaluated. This strategy is available for finite search spaces only.
* Bad-configuration-basedSC is satisfied when the total number of invalid configurations reaches a user-defined limit. 
* Few-shot-learning-based SC is triggered when the current best configuration has been provided by the transfer learning component. 
* Guaranteed SC is fired when the current best configuration provides a better objective function value than the default configuration.
* Improvement-based SC is satisfied in case when the solution has not been improved for a user-defined number of successive iterations.
* Quantity-based SC is triggered when the number of evaluated configurations is greater than a user-defined value.
* Time-based SC is fired when a specified maximal time limit is reached.
* Validation-based SC is satisfied when a surrogate model that is used for the experiment passes a validity check.

Each `Stop Condition` has an attribute `Name` which plays role of a unique ID.
* `StopConditionTriggerLogic` is a feature in which the user could specify any logic of BRISE Experiment termination by composing the operands 
`and`, `or`, brackets `(` `)` and names of Stop Conditions into a single expression.

**WARNING: Stop Conditions, that are configured, but not used in `StopConditionTriggerLogic` are ignored.**

#### Transfer Learning
is an optional component, responsible for reuse of the knowledge gathered during previous optimization runs.

For a detailed description of this component consult the respective [documentation page](../../main_node/transfer_learning/README.md)

#### Default Configuration Handler
is an optional component, which can be used, when the experiment designer 1) does not possess an intuition on which configuration to be used as the default; or 2) possesses a custom approach in determining the starting configuration. 
In BRISE v2.6.0, we offer only one general variant of this feature: \texttt{Random Default Configuration Handler}, which picks the starting configuration using the Mersenne Twister algorithm. 

## Product configuration

Product configuration process is performed with [Waffle component](../../waffle/README.md).

Exemplary product configurations can be found [here](tests/test_cases_product_configurations).