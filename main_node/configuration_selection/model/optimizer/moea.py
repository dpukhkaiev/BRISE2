from typing import Tuple, Dict, List
import pandas as pd
import numpy as np
import pygmo as pg

from core_entities.search_space import NumericHyperparameter
from core_entities.search_space import CategoricalHyperparameter

from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate

# these algorithms may leave the bounds of the problem unless explicitly forced to respect them
FORCE_BOUNDS_ALGORITHMS = frozenset({"cmaes", "xnes"})


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
        # which surrogate a categorical hyperparameter's transformer was borrowed from is only known per optimize()
        # call, so bounds/params/masked_params/_borrowed_config_transformer_parameter are (re)built there
        self._borrowed_config_transformer_parameter: Dict[ConfigurationTransformer, Tuple] = {}

    def _resolve_categorical_transform(self, hp, surrogate: Surrogate, borrowed: Dict):
        """
        A MOEA optimizer needs numeric bounds even for a categorical hyperparameter its own
        ConfigurationTransformers don't cover, so fall back to the paired surrogate's transformer for it.
        """
        if any(hp in params for params in self.mapping_config_transformer_parameter.values()):
            return self._transform_configuration
        for ct, params in surrogate.mapping_config_transformer_parameter.items():
            if hp in params:
                borrowed[ct] = params
                return surrogate._transform_configuration
        raise ValueError(
            f"MOEA cannot resolve numeric bounds for categorical hyperparameter '{hp.name}': it is covered by "
            f"neither the optimizer's own ConfigurationTransformers nor the paired Surrogate's "
            f"('{type(surrogate).__name__}')."
        )

    def _build_bounds_params_masked(self, surrogate: Surrogate) -> None:
        bounds: Tuple[List, List] = ([], [])
        params: List[str] = []
        masked_params: Dict[str: Tuple[float, int]] = {}
        borrowed: Dict[ConfigurationTransformer, Tuple] = {}

        i = 0  # number of masked parameters within the region influencing indexing of subsequent masked parameters
        for hp in self.region:
            if issubclass(type(hp), NumericHyperparameter):
                lower = hp.transform(0)
                lower_hp = pd.DataFrame([lower], columns=[hp.name])
                upper = hp.transform(1)
                upper_hp = pd.DataFrame([upper], columns=[hp.name])
                hps = pd.merge(lower_hp, upper_hp, how='outer')

                transformed_hps = self._transform_configuration(hps)

                transformed_name = transformed_hps.columns[0]
                bounds[0].append(transformed_hps.loc[0][transformed_name])
                bounds[1].append(transformed_hps.loc[1][transformed_name])
                params.append(transformed_name)

            if issubclass(type(hp), CategoricalHyperparameter):
                transform_fn = self._resolve_categorical_transform(hp, surrogate, borrowed)

                transformed_variants = pd.DataFrame()
                for category in hp.categories:
                    variant = pd.DataFrame([category], columns=[hp.name])
                    transformed_variant = transform_fn(variant)
                    if transformed_variants.empty:
                        transformed_variants = transformed_variant
                    else:
                        transformed_variants = pd.concat([transformed_variants, transformed_variant])
                for c in transformed_variants.columns:
                    if min(transformed_variants[c]) == max(transformed_variants[c]):
                        masked_params[c] = tuple([min(transformed_variants[c]), len(params) + i])
                        i += 1
                        continue
                    bounds[0].append(min(transformed_variants[c]))
                    bounds[1].append(max(transformed_variants[c]))
                    params.append(c)

        self.bounds, self.params, self.masked_params = bounds, params, masked_params
        self._borrowed_config_transformer_parameter = borrowed

    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        self._build_bounds_params_masked(surrogate)
        problem = self._PygmoProblem(optimizer=self, surrogate=surrogate)
        population = pg.population(problem, self.pop_size)
        for algo_name in self.algorithms:
            algo_parameters = {"gen": self.generations}
            if algo_name in FORCE_BOUNDS_ALGORITHMS:
                algo_parameters["force_bounds"] = True
            algo = pg.algorithm(getattr(pg, algo_name)(**algo_parameters))
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

    def _inverse_transform_configuration(self, optimized_features: pd.DataFrame) -> pd.DataFrame:
        result = super()._inverse_transform_configuration(optimized_features)
        for ct, _ in self._borrowed_config_transformer_parameter.items():
            for _, new_f in ct.mapping_old_new_features.items():
                if not any(c in optimized_features.columns for c in new_f):
                    continue
                inverse_transformed = ct.inverse_transform(optimized_features[new_f])
                result = result.drop(columns=[c for c in new_f if c in result.columns], errors="ignore")
                result = inverse_transformed if result.empty else result.join(inverse_transformed)
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
