from typing import Tuple, Dict, List
import pandas as pd
import numpy as np
import pygmo as pg

from core_entities.search_space import NumericHyperparameter
from core_entities.search_space import CategoricalHyperparameter

from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate


class MOEA(Optimizer):
    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(optimizer_description, region, objectives)
        self.generations = optimizer_description["Instance"][self.feature_name]["Generations"]
        self.pop_size = optimizer_description["Instance"][self.feature_name]["PopulationSize"]
        self.algorithms = []
        for a in optimizer_description["Instance"][self.feature_name]["Algorithms"]:
            self.algorithms.append(a.lower())

        # transform and get boundaries
        self.bounds: Tuple[List, List] = ([], [])
        self.params: List[str] = []
        self.masked_params: Dict[str: Tuple[float, int]] = {}  # if lower bound == upper bound nsga2 and moead don't work

        i = 0  # number of masked parameters within the region influencing indexing of subsequent masked parameters
        for hp in region:
            if issubclass(type(hp), NumericHyperparameter):
                lower = hp.transform(0)
                lower_hp = pd.DataFrame([lower], columns=[hp.name])
                upper = hp.transform(1)
                upper_hp = pd.DataFrame([upper], columns=[hp.name])
                hps = pd.merge(lower_hp, upper_hp, how='outer')

                transformed_hps = self._transform_configuration(hps)

                transformed_name = transformed_hps.columns[0]
                self.bounds[0].append(transformed_hps.loc[0][transformed_name])
                self.bounds[1].append(transformed_hps.loc[1][transformed_name])
                self.params.append(transformed_name)

            if issubclass(type(hp), CategoricalHyperparameter):
                transformed_variants = pd.DataFrame()
                for category in hp.categories:
                    variant = pd.DataFrame([category], columns=[hp.name])
                    transformed_variant = self._transform_configuration(variant)
                    if transformed_variants.empty:
                        transformed_variants = transformed_variant
                    else:
                        transformed_variants = pd.concat([transformed_variants, transformed_variant])
                for c in transformed_variants.columns:
                    if min(transformed_variants[c]) == max(transformed_variants[c]):
                        self.masked_params[c] = tuple([min(transformed_variants[c]), len(self.params) + i])
                        i += 1
                        continue
                    self.bounds[0].append(min(transformed_variants[c]))
                    self.bounds[1].append(max(transformed_variants[c]))
                    self.params.append(c)

    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        problem = self._PygmoProblem(optimizer=self, surrogate=surrogate)
        population = pg.population(problem, self.pop_size)
        for algo_name in self.algorithms:
            algo = pg.algorithm(getattr(pg, algo_name)(gen=self.generations))
            population = algo.evolve(population)

        optimized_features = pd.DataFrame(population.get_x(), columns=self.params)
        if surrogate.scalarized:
            optimized_labels = pd.DataFrame(population.get_f(), columns=["Y"])
        else:
            optimized_labels = pd.DataFrame(population.get_f(), columns=list(self.objectives.keys()))

        for p, val_ind in self.masked_params.items():
            optimized_features.insert(loc=val_ind[1], column=p, value=val_ind[0])

        optimized_features = self._inverse_transform_configuration(optimized_features)  # inverse transform

        result = optimized_features.join(optimized_labels)
        return result

    class _PygmoProblem:
        """
        A custom Pygmo problem, where the surrogate is utilized to evaluate the objective function.
        """
        def __init__(self,
                     optimizer,
                     surrogate: Surrogate):
            self._surrogate = surrogate
            self._optimizer: MOEA = optimizer
            self._bounds = self._optimizer.bounds
            self._objectives = self._optimizer.objectives
            self._params = self._optimizer.params
            self._transform_surrogate, self._inverse_transform_optimizer = (
                self._optimizer._resolve_configuration_transformers(surrogate))

        def fitness(self, x):
            temp_params = self._params.copy()
            temp_x = x
            for p, val_ind in self._optimizer.masked_params.items():
                temp_params.insert(val_ind[1], p)
                temp_x = np.insert(temp_x, val_ind[1], val_ind[0])
            x = dict(map(lambda i, j: (i, j), temp_params, temp_x))

            x = pd.Series(x)

            if self._inverse_transform_optimizer:
                x_df = pd.DataFrame(columns=x.index)
                x_df.loc[0] = x.values
                x_df = self._optimizer._inverse_transform_configuration(x_df)
                x = x_df.loc[0]

            result = self._surrogate.predict(x, self._transform_surrogate)

            transformed_result = self._optimizer._transform_values(result)
            return transformed_result.values.flatten().tolist()

        def get_nobj(self):
            return len(self._objectives) if not self._surrogate.scalarized else 1

        def get_bounds(self):
            return self._bounds
