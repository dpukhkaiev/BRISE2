import logging
import pickle
import os
from typing import List, Mapping, Set, Tuple

import pandas as pd

from configuration_selection.sampling.sampling_strategy_orchestrator import SamplingStrategyOrchestrator
from core_entities.configuration import Configuration
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
            type = models_types[level]  # TODO Enable region-wise model type assignment
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

    def predict(self, measured_configurations: List[Configuration], sample: bool = False) -> List[Configuration]:
        """
        Predict or sample one or multiple configurations
        :param measured_configurations: list of already measured configurations
        :param sample: whether to fully sample or do a surrogate-based prediction
        :return: list of predicted configurations
        """

        # information for transfer learning
        prediction_info = {}
        model_dump = []  # a combination of models for hierarchical search space

        configuration_type = Configuration.Type.PREDICTED

        # calculating configurations to be used by the prediction
        number_of_configs_to_consider = int(round(self.window_size * len(measured_configurations)))
        considered_configs = measured_configurations[-number_of_configs_to_consider:]

        activated_regions = self.search_space.get_regions_on_current_level()
        assert len(activated_regions) == 1

        predicted = pd.DataFrame()
        considered_hp_names = []

        while len(activated_regions) > 0:
            self.search_space.next_level()
            next_activated_regions: Set[Tuple[Hyperparameter]] = set()
            for region in activated_regions:
                if not sample:
                    considered_hp_names_in_region = [hp.name for hp in region]
                    considered_hp_names += considered_hp_names_in_region
                    considered_activation_category = [hp.activation_category for hp in region][0]
                    considered_parent_hp_name = [hp.parent.name for hp in region][0]

                    # filter according to the considered activation category for the current region
                    if considered_parent_hp_name != "root":
                        considered_configs = list(filter(lambda cfg:
                               cfg.parameters[considered_parent_hp_name] == considered_activation_category,
                               considered_configs))
                    # filter according to the region
                    if len(considered_configs) > 0 and considered_parent_hp_name != "root":
                        logging.info("Considered Configs: " + " ".join([c.__str__() for c in considered_configs]))
                        logging.info("REGION: " + str(region.__str__()))
                    considered_configs = list(filter(
                        lambda cfg: any(map(lambda x: x in considered_hp_names_in_region, list(cfg.parameters.keys()))),
                        considered_configs  # Input data for filter
                    ))
                    # TODO prediction of multiple configurations is not handled
                    partial_configuration = self.mapping_region_model[region].predict(list(region), considered_configs)

                    if partial_configuration.empty:
                        configuration_type = Configuration.Type.FROM_SELECTOR
                        partial_configuration = self.mapping_region_sampling_strategy[region].sample()
                        if predicted.empty:
                            predicted = partial_configuration
                        else:
                            # in case on one level of the search space model offered several configurations,
                            # while on another level, sampling was performed; sampled config must be multiplied
                            # to merge into a set of full configurations
                            multiplied_partial_configuration = pd.DataFrame()
                            for i in range(len(predicted.index)):
                                if multiplied_partial_configuration.empty:
                                    multiplied_partial_configuration = partial_configuration
                                else:
                                    multiplied_partial_configuration.loc[i] = partial_configuration.values[0]
                            # since sampling has been used, there are no objective function values and merge is safe
                            predicted = pd.merge(predicted, partial_configuration, left_index=True, right_index=True)
                    else:
                        if predicted.empty:
                            predicted = partial_configuration
                        else:
                            # TODO develop a strategy for merging objectives on different levels.
                            #  Problem: merging scalarized with regular predictions
                            #  Corrupts statistics, but doesn't influence optimization
                            predicted = pd.merge(predicted, partial_configuration, left_index=True, right_index=True)
                else:
                    configuration_type = Configuration.Type.FROM_SELECTOR
                    partial_configuration = self.mapping_region_sampling_strategy[region].sample()
                    if predicted.empty:
                        predicted = partial_configuration
                    else:
                        predicted = predicted.join(partial_configuration)
                if len(next_activated_regions) == 0:
                    # TODO handle multiple predicted configurations.
                    #  multiple regions can be activated by different configs, which breaks next iteration
                    next_activated_regions = self.search_space.activate_regions(predicted)
                else:
                    next_activated_regions.update(self.search_space.activate_regions(predicted))

                region_index = str(self.search_space.regions.index(region))
                prediction_info[region_index] = {
                    "Model": self.mapping_region_model[region].created_surrogates_descriptions_and_objectives_and_optimizer_descriptions,
                    "time_to_build": self.mapping_region_model[region].time_to_build
                    if self.mapping_region_model[region].time_to_build is not None else 0}
                if self.mapping_region_model[region].time_to_build is not None:
                    model_dump.append(pickle.dumps(self.mapping_region_model[region]))

            activated_regions = next_activated_regions

        predicted_configurations = []
        for i, f in predicted.iterrows():
            if not sample:
                parameters = f.drop(predicted.columns.difference(considered_hp_names)).to_dict()
                predicted_values = f.drop(considered_hp_names).to_dict()
            else:
                parameters = f.to_dict()
                predicted_values = {}
            configuration = Configuration(parameters, configuration_type, self.experiment_id, prediction_info=prediction_info)
            configuration.predicted_result = list(predicted_values.values())
            predicted_configurations.append(configuration)

        self.search_space.reset_level()
        msg = f"CONFIGURATION STATUS: {configuration_type}"
        self.logger.info(msg)

        if len(model_dump) == self.search_space.number_of_levels:
            self.hierarchical_models_dumps.append(model_dump)

        self.store_model_dumps_to_db()
        return predicted_configurations

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
