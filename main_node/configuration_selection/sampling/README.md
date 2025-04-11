# Sampling Strategy
The sampling strategy is a mandatory feature of BRISE which is used for model-less configuration selection.

This folder contains an [abstract sampling strategy class](selection_algorithm_abs.py) which is responsible for sampling parameters values;
and its concrete variants, which represent different strategies. Moreover, it contains a [SamplingStrategyOrchestrator](sampling_strategy_orchestrator.py) class, 
which instantiates the exact strategy based on the SPL configuration. 
 
In its current implementation two strategies are available:
 
 ## Mersenne-twister
Mersenne Twister is a uniform pseudo-random number generator.
 
 ## Sobol sequence
 Sobol sampling is a uniform, quasi-random sequence in multidimensional space. 

## Extension 
To add your own sampling strategy, create a separate Python-file in this folder with a class that extends the `SamplingStrategy` class, and implement the `sample(...)` method. 
The new strategy won't go through the validation process until you include it into the  [feature model](../../Resources/test/waffle_models/base.wfl).

## Important note
The return value of the `sample(...)` method must be a pandas.Dataframe, 
which can be created by the `transform(...)` method within the [base class](selection_algorithm_abs.py).
