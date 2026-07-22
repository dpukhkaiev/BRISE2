import logging
import pickle
import os
from collections import defaultdict
from typing import Dict, List, Mapping, Tuple

import pandas as pd

from configuration_selection.sampling.sampling_strategy_orchestrator import SamplingStrategyOrchestrator
from core_entities.configuration import Configuration, PartialConfiguration
from core_entities.search_space import Hyperparameter
from core_entities.search_space import SearchSpace
from tools.mongo_dao import MongoDB
from configuration_selection.model.model import Model


class Predictor:
    """
    This class abstract notion of prediction within tree-shaped search space from the underlying models.
    The underlying models see only the current level with related data that is going to be operated in it,
    no other level data exposed for it.

    Responsibilities:
        - hide structure of tree-shaped search space.
        - provide data and data description for underlying models about current level.
        - select underlying model for each level
    """
    def __init__(self,
                 experiment_id: str,
                 experiment_description: Mapping,
                 search_space: SearchSpace):
        self.experiment_id = experiment_id
        self.predictor_config = experiment_description["ConfigurationSelection"]["Predictor"]
        self.task_config = experiment_description["Context"]["TaskConfiguration"]
        self.search_space = search_space
        self.window_size = self.predictor_config["WindowSize"]
        self.sampling_strategy_orchestrator = SamplingStrategyOrchestrator()

        self.logger = logging.getLogger(__name__)

        models_types = []
        for i in self.predictor_config.items():
            if "Model" in i[0]:
                models_types.append(i)

        self.mapping_region_model = {}
        for r in self.search_space.regions:
            level = r[0].level
            type = models_types[level]
            model = Model(model_description=type, region=r, objectives=self.task_config["Objectives"])
            self.mapping_region_model[r] = model

        self.mapping_region_sampling_strategy = {}
        for r in self.search_space.regions:
            sampling_strategy = (self.sampling_strategy_orchestrator.
                                 get_sampling_strategy
                                 (experiment_description["ConfigurationSelection"]["SamplingStrategy"], r))
            self.mapping_region_sampling_strategy[r] = sampling_strategy

        self.hierarchical_models_dumps = []

        self.logger = logging.getLogger(__name__)

    @property
    def number_of_points(self) -> int:
        """
        The number of configurations a single proposal yields (NumberOfPoints).

        Every level has its own Model, hence its own CandidateSelector. They must
        agree, otherwise a point could reach a region that cannot serve it a
        candidate of its own.
        """
        points = {model.candidate_selector.number_of_points for model in self.mapping_region_model.values()}
        if len(points) > 1:
            raise ValueError(f"All levels must propose the same NumberOfPoints, got {sorted(points)}.")
        return points.pop()

    def predict(self, measured_configurations: List[Configuration], sample: bool = False) -> List[Configuration]:
        """
        Predict or sample one or multiple configurations.

        The search space is walked level by level, carrying `number_of_points`
        partial configurations. Every region that at least one point activated is
        built and optimized exactly ONCE, and the candidate rows of that single
        proposal are handed out among the points waiting for it. Points therefore
        share the optimizer's work instead of each triggering their own run, and
        each stays on the single branch it activated.

        :param measured_configurations: list of already measured configurations
        :param sample: whether to fully sample or do a surrogate-based prediction
        :return: list of predicted configurations
        """
        # information for transfer learning
        prediction_info = {}
        model_dump = []  # a combination of models for hierarchical search space

        # calculating configurations to be used by the prediction
        number_of_configs_to_consider = int(round(self.window_size * len(measured_configurations)))
        considered_configs = measured_configurations[-number_of_configs_to_consider:]

        root_regions = self.search_space.get_regions_on_current_level()
        assert len(root_regions) == 1

        # Sampling is a fallback for a single duplicate-breaking configuration,
        # a proposal of several points is only asked of the models.
        number_of_points = 1 if sample else self.number_of_points
        points = [PartialConfiguration(pending_regions=set(root_regions)) for _ in range(number_of_points)]

        while any(point.pending_regions for point in points):
            self.search_space.next_level()
            for region, waiting_points in self._subscriptions(points).items():
                candidates, is_sampled = self._propose(region, considered_configs, len(waiting_points), sample)
                if not is_sampled:
                    self._record_model(region, prediction_info, model_dump)

                for i, point in enumerate(waiting_points):
                    candidate = candidates.iloc[i % len(candidates)]
                    point.absorb(candidate, region)
                    if is_sampled:
                        point.type = Configuration.Type.FROM_SELECTOR
                    point.pending_regions |= self.search_space.activate_regions(candidate.to_frame().T)

        self.search_space.reset_level()
        self.logger.info(f"Proposal walked the search space for {number_of_points} point(s) "
                         f"(NumberOfPoints={self.number_of_points}, sample={sample}).")

        if len(model_dump) == self.search_space.number_of_levels:
            self.hierarchical_models_dumps.append(model_dump)

        self.store_model_dumps_to_db()
        return [point.to_configuration(self.experiment_id, prediction_info) for point in points]

    @staticmethod
    def _subscriptions(points: List[PartialConfiguration]) -> Dict[Tuple[Hyperparameter], List[PartialConfiguration]]:
        """Invert the points' pending regions: which points wait for which region on this level."""
        subscriptions = defaultdict(list)
        for point in points:
            for region in point.pending_regions:
                subscriptions[region].append(point)
            point.pending_regions = set()
        return subscriptions

    def _propose(self, region: Tuple[Hyperparameter], considered_configs: List[Configuration],
                 number_of_points: int, sample: bool) -> Tuple[pd.DataFrame, bool]:
        """
        Propose candidates for one region: one surrogate build and one optimizer
        run, or `number_of_points` sampled rows if a model cannot be built.

        :return: the candidate rows and whether they were sampled
        """
        if not sample:
            candidates = self.mapping_region_model[region].predict(
                list(region), self._configs_within_region(region, considered_configs))
            if not candidates.empty:
                return candidates.reset_index(drop=True), False

        samples = [self.mapping_region_sampling_strategy[region].sample() for _ in range(number_of_points)]
        return pd.concat(samples, ignore_index=True), True

    @staticmethod
    def _configs_within_region(region: Tuple[Hyperparameter],
                               considered_configs: List[Configuration]) -> List[Configuration]:
        """Keep the measured configurations that lie on this region's branch and carry its parameters."""
        region_hp_names = [hp.name for hp in region]
        parent_hp_name = region[0].parent.name
        activation_category = region[0].activation_category

        if parent_hp_name != "root":
            considered_configs = [cfg for cfg in considered_configs
                                  if cfg.parameters.get(parent_hp_name) == activation_category]
        return [cfg for cfg in considered_configs if any(name in region_hp_names for name in cfg.parameters)]

    def _record_model(self, region: Tuple[Hyperparameter], prediction_info: Dict, model_dump: List) -> None:
        model = self.mapping_region_model[region]
        region_index = str(self.search_space.regions.index(region))
        prediction_info[region_index] = {
            "Model": model.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions,
            "time_to_build": model.time_to_build if model.time_to_build is not None else 0}
        if model.time_to_build is not None:
            model_dump.append(pickle.dumps(model))

    def store_model_dumps_to_db(self):
        # initialize connection to the database
        database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                           os.getenv("BRISE_DATABASE_PORT"),
                           os.getenv("BRISE_DATABASE_NAME"),
                           os.getenv("BRISE_DATABASE_USER"),
                           os.getenv("BRISE_DATABASE_PASS"))
        if database.get_last_record_by_experiment_id("Transfer_learning_info", self.experiment_id) is None:
            database.write_one_record("Transfer_learning_info",
                                      {"Exp_unique_ID": self.experiment_id,
                                       "Models_dumps": self.hierarchical_models_dumps})
        else:
            database.update_record(
                "Transfer_learning_info",
                {"Exp_unique_ID": self.experiment_id},
                {"Models_dumps": self.hierarchical_models_dumps})

    def update_mapping_region_model(self, transferred_mapping_region_model):
        """
        Update the models, based on the transfer learning results. Assumption: regions are identical
        """
        for current_region in self.mapping_region_model.keys():
            for transferred_region in transferred_mapping_region_model.keys():
                if transferred_region == current_region:
                    self.mapping_region_model[current_region] = transferred_mapping_region_model[transferred_region]
