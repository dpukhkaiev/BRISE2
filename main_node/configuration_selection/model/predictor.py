import logging
import pickle
import os
from typing import Dict, List, Mapping, Set, Tuple

import pandas as pd

from configuration_selection.sampling.sampling_strategy_orchestrator import SamplingStrategyOrchestrator
from core_entities.configuration import Configuration
from core_entities.search_space import Hyperparameter
from core_entities.search_space import SearchSpace
from tools.mongo_dao import MongoDB
from configuration_selection.model.model import Model

REGION_COLUMN_SUFFIX = "__region"


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
        base_considered_configs = measured_configurations[-number_of_configs_to_consider:]

        activated_regions = self.search_space.get_regions_on_current_level()
        assert len(activated_regions) == 1

        predicted = pd.DataFrame()
        considered_hp_names = []

        while len(activated_regions) > 0:
            self.search_space.next_level()
            next_activated_regions: Set[Tuple[Hyperparameter]] = set()
            for region in activated_regions:
                region_index = str(self.search_space.regions.index(region))
                if not sample:
                    considered_hp_names_in_region = [hp.name for hp in region]
                    considered_hp_names += considered_hp_names_in_region

                    region_considered_configs = self._considered_configs_for_region(
                        base_considered_configs, region, considered_hp_names_in_region)
                    if len(region_considered_configs) > 0:
                        logging.info("Considered Configs: " +
                                     " ".join([c.__str__() for c in region_considered_configs]))
                        logging.info("REGION: " + str(region.__str__()))
                    partial_configuration = self.mapping_region_model[region].predict(
                        list(region), region_considered_configs)

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
                            predicted = pd.merge(predicted, multiplied_partial_configuration, left_index=True, right_index=True)
                    else:
                        predicted = self._update_prediction(predicted, partial_configuration, region_index,
                                                                   considered_hp_names_in_region)
                else:
                    configuration_type = Configuration.Type.FROM_SELECTOR
                    partial_configuration = self.mapping_region_sampling_strategy[region].sample()
                    if predicted.empty:
                        predicted = partial_configuration
                    else:
                        predicted = predicted.join(partial_configuration)
                if len(next_activated_regions) == 0:
                    next_activated_regions = self.search_space.activate_regions(predicted)
                else:
                    next_activated_regions.update(self.search_space.activate_regions(predicted))

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
                predicted_values = self._average_predictions_per_objective(f.drop(considered_hp_names))
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

    def _considered_configs_for_region(self, base_considered_configs: List[Configuration],
                                        region: Tuple[Hyperparameter],
                                        considered_hp_names_in_region: List[str]) -> List[Configuration]:
        """
        Scope the base window of considered configurations down to the ones relevant to one region,
        always starting from the untouched base window so sibling/deeper regions never inherit another
        region's filtering.
        """
        considered_activation_category = region[0].activation_category
        considered_parent_hp_name = region[0].parent.name

        region_considered_configs = base_considered_configs
        if considered_parent_hp_name != "root":
            # a config on a different branch simply does not have this parent hyperparameter measured;
            # it does not belong to this region rather than being an error
            region_considered_configs = list(filter(
                lambda cfg: cfg.parameters.get(considered_parent_hp_name) == considered_activation_category,
                region_considered_configs))
        region_considered_configs = list(filter(
            lambda cfg: any(x in considered_hp_names_in_region for x in cfg.parameters.keys()),
            region_considered_configs))
        return region_considered_configs

    def _update_prediction(self, predicted: pd.DataFrame, partial_configuration: pd.DataFrame,
                                  region_index: str, considered_hp_names_in_region: List[str]) -> pd.DataFrame:
        """
        Update prediction with a partial configuration. Objective columns are renamed region-wise for merging.  
        """
        if predicted.empty:
            return partial_configuration
        objective_columns = partial_configuration.columns.difference(considered_hp_names_in_region)
        partial_configuration = partial_configuration.rename(
            columns={c: f"{c}{REGION_COLUMN_SUFFIX}{region_index}" for c in objective_columns})
        return pd.merge(predicted, partial_configuration, left_index=True, right_index=True)

    def _average_predictions_per_objective(self, predicted_values: pd.Series) -> Dict[str, float]:
        """
        Every region's model predicts all objectives, they are merged into a single value per objective. 
        """
        values_per_objective: Dict[str, List[float]] = {}
        for column_name in predicted_values.index:
            objective_name = column_name.split(REGION_COLUMN_SUFFIX)[0]
            if objective_name not in values_per_objective:
                values_per_objective[objective_name] = []
            values_per_objective[objective_name].append(predicted_values[column_name])

        averaged_values = {}
        for objective_name, values in values_per_objective.items():
            averaged_values[objective_name] = sum(values) / len(values)
        return averaged_values

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
