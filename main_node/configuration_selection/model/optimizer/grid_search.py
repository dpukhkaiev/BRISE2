"""Grid Search Optimizer

This module implements a grid search optimizer that systematically explores
the search space by evaluating configurations on a regular grid.
"""

from typing import Tuple, Dict, List
import pandas as pd
import numpy as np
import itertools

from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from core_entities.search_space import Hyperparameter


class GridSearch(Optimizer):
    """Grid search optimizer for systematic search space exploration"""

    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Dict):
        """
        Initialize grid search optimizer.

        Args:
            optimizer_description: Optimizer configuration dictionary
            region: Tuple of hyperparameters defining the search space
            objectives: Dictionary of optimization objectives
        """
        super().__init__(optimizer_description, region, objectives)

        instance_config = optimizer_description["Instance"][self.feature_name]
        self.grid_resolution = instance_config.get("GridResolution", 5)
        self.max_grid_points = instance_config.get("MaxGridPoints", 10000)

    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        """
        Generate and evaluate grid points.

        Args:
            surrogate: Surrogate model for prediction

        Returns:
            DataFrame with evaluated configurations
        """
        # Generate grid configurations
        grid_configs = self._generate_grid()

        if len(grid_configs) == 0:
            raise ValueError("Grid generation produced no configurations")

        # Evaluate all configurations
        predicted = pd.DataFrame()
        for config_dict in grid_configs:
            # Convert to Series
            config_series = pd.Series(config_dict)

            # Predict value using surrogate
            prediction = surrogate.predict(config_series)

            # Combine configuration and prediction
            config_df = pd.DataFrame([config_dict])
            evaluated = config_df.join(prediction)
            predicted = pd.concat([predicted, evaluated], ignore_index=True)

        return predicted

    def _generate_grid(self) -> List[Dict]:
        """
        Generate grid configurations based on search space.

        Returns:
            List of configuration dictionaries
        """
        # Separate parameters by type
        float_params = []
        int_params = []
        categorical_params = []

        for param in self.region:
            if param.type == "FloatHyperparameter":
                float_params.append(param)
            elif param.type == "IntegerHyperparameter":
                int_params.append(param)
            elif param.type == "NominalHyperparameter":
                categorical_params.append(param)

        # Generate grid values for each parameter
        param_grids = {}

        for param in float_params:
            param_grids[param.name] = self._generate_float_grid(param)

        for param in int_params:
            param_grids[param.name] = self._generate_int_grid(param)

        for param in categorical_params:
            param_grids[param.name] = self._generate_categorical_grid(param)

        # Check total grid size
        total_points = np.prod([len(values) for values in param_grids.values()])

        if total_points > self.max_grid_points:
            # Use adaptive strategy for large grids
            return self._generate_adaptive_grid(param_grids, total_points)

        # Generate all combinations
        param_names = list(param_grids.keys())
        param_values = [param_grids[name] for name in param_names]

        configurations = []
        for combination in itertools.product(*param_values):
            config = {name: value for name, value in zip(param_names, combination)}
            configurations.append(config)

        return configurations

    def _generate_float_grid(self, param: Hyperparameter) -> List[float]:
        """Generate grid values for a float parameter"""
        lower = getattr(param, 'lower', 0.0)
        upper = getattr(param, 'upper', 1.0)
        return np.linspace(lower, upper, self.grid_resolution).tolist()

    def _generate_int_grid(self, param: Hyperparameter) -> List[int]:
        """Generate grid values for an integer parameter"""
        lower = getattr(param, 'lower', 0)
        upper = getattr(param, 'upper', 10)

        # Determine number of points (don't exceed range)
        n_points = min(self.grid_resolution, upper - lower + 1)

        if n_points <= 0:
            return [lower]

        # Generate evenly spaced integers
        if n_points == upper - lower + 1:
            # Use all integers in range
            return list(range(lower, upper + 1))
        else:
            # Sample evenly
            values = np.linspace(lower, upper, n_points)
            return [int(round(v)) for v in values]

    def _generate_categorical_grid(self, param: Hyperparameter) -> List[str]:
        """Generate grid values for a categorical parameter"""
        # Return all categories
        if hasattr(param, 'categories'):
            return param.categories
        elif hasattr(param, 'default'):
            # Fallback: just use default if categories not available
            return [param.default]
        else:
            return []

    def _generate_adaptive_grid(
        self,
        param_grids: Dict[str, List],
        total_points: int
    ) -> List[Dict]:
        """
        Generate adaptive grid when full grid is too large.

        Uses a coarser grid or Latin Hypercube sampling strategy.

        Args:
            param_grids: Dictionary mapping parameter names to grid values
            total_points: Total number of points in full grid

        Returns:
            List of configuration dictionaries
        """
        # Calculate reduction factor needed
        reduction_factor = (total_points / self.max_grid_points) ** (1.0 / len(param_grids))

        # Reduce grid resolution for each parameter
        reduced_grids = {}
        for param_name, values in param_grids.items():
            if len(values) > 1:
                new_size = max(2, int(len(values) / reduction_factor))
                # Sample evenly from the grid
                indices = np.linspace(0, len(values) - 1, new_size, dtype=int)
                reduced_grids[param_name] = [values[i] for i in indices]
            else:
                reduced_grids[param_name] = values

        # Generate configurations from reduced grid
        param_names = list(reduced_grids.keys())
        param_values = [reduced_grids[name] for name in param_names]

        configurations = []
        for combination in itertools.product(*param_values):
            config = {name: value for name, value in zip(param_names, combination)}
            configurations.append(config)

        # If still too large, sample randomly
        if len(configurations) > self.max_grid_points:
            indices = np.random.choice(
                len(configurations),
                self.max_grid_points,
                replace=False
            )
            configurations = [configurations[i] for i in indices]

        return configurations
