# Selection algorithm
The selection algorithm is a mandatory feature of BRISE which is used for random configuration sampling.

This folder contains an abstract selection algorithm class (`selection_algorithm_abs.py`) which is responsible for sampling parameters value;
and its concrete variants, which represent different selection strategies. Moreover, it contains a `selection_algorithms.py` file, 
which instantiates the exact selection algorithm based on user preferences from the `SettingsBRISE.json` file. 
 
In its current implementation two strategies are available:
 
 ## Mersenne-twister selection algorithm
 This strategy generates a single number using Mersenne-twister pseudo-random generator.
 
 ## Sobol sequence
 This strategy generates the Sobol vector using the `dimensionality` parameter as vector length, `configuration_number` as seed number. 
 It returns a single value respective to the `dimension` parameter which reflects the parameter sequence number.
 
## Example of SelectionAlgorithm field of `SettingBRISE.json` file
 ```json
  "SelectionAlgorithm": "MersenneTwister",
```

## Extension 
To add your own selection algorithm, create a separate python-file in this folder with a class that extends the `SelectionAlgorithm` class, and implement the `get_value(...)` method. 
The new strategy won't go through the validation process until you register it in [experiment schema](./../Resources/schema/experiment.schema.json).

## Important note
The return value of `get_value(...)` method should be `float` type in range `[0...1]`.
An additional transformation to search space boundaries is performed in the `Search Space` module.