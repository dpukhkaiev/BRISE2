import logging
import json
import os
from typing import List, Tuple
from copy import deepcopy

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from configuration_selection.model.predictor import Predictor
from tools.front_API import API
from tools.rabbitmq_common_tools import RabbitMQConnection, publish
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator


class ConfigurationSelection:
    """
    Orchestration class for Configuration Selection module.
    """

    def __init__(self, experiment: Experiment):
        self.sub = API()
        self.experiment = experiment

        self.predictor: Predictor = Predictor(
            self.experiment.unique_id,
            self.experiment.description,
            self.experiment.search_space
        )
        # check if TL is available
        if "TransferLearning" in self.experiment.description.keys():
            self.transfer_is_enabled = True
            self.transfer_learning_orchestrator = TransferLearningOrchestrator(self.experiment.description,
                                                                               self.experiment.unique_id)
        else:
            self.transfer_is_enabled = False

        self.logger = logging.getLogger(__name__)
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.connection_thread = self._EventServiceConnection(self)
            self.connection_thread.start()

    def send_new_configurations_to_measure(self, ch, method, properties, body) -> Tuple[
            List[Configuration], List[Configuration]]:
        """
        This callback function will be triggered upon arrival of EACH measured Configuration.
        When there is new measured Configuration, the following steps are done:

            1.   the surrogates are updated and validated
            2.   configuration(s) selection either by the surrogate, or by the sampling strategy:
                Note: The number of new configurations can be:
                - 0 if the number of the available Worker nodes has decreased;
                - 1 if the number of the available Workers has not changed;
                - N + 1 if the number of the available Workers has increased by N.
            3.   new configuration(s) are sent to the Repetition Manager for evaluation.

        :return: FOR TESTING ONLY: Two lists:
                                * configs_to_be_evaluated: contains all parameters for the flat search space
                                * hierarchical_configs: the way a configuration is being sent to the worker
        """
        needed_configs = json.loads(body.decode()).get("worker_capacity", 1)

        number_of_predicted_configs = (
            min([model.candidate_selector.number_of_points for model in self.predictor.mapping_region_model.values()]))

        predicted_configs = []
        configs_to_be_evaluated = []

        if not self.transfer_is_enabled:
            predicted_configs.extend(self._regular_prediction(needed_configs, number_of_predicted_configs))
        else:
            similar_experiments = self.transfer_learning_orchestrator.ted_module.analyse_experiments_similarity()
            if similar_experiments is None:
                sampled_config = self.predictor.predict(self.experiment.measured_configurations, True)[0]
                predicted_configs.append(sampled_config)
                temp_msg = f"Transfer expediency cannot be determined yet. Sampled: {sampled_config}."
                self.logger.info(temp_msg)
            elif len(similar_experiments) == 0:
                temp_msg = "No similar experiment has been found."
                self.logger.info(temp_msg)
                predicted_configs.extend(self._regular_prediction(needed_configs, number_of_predicted_configs))
            else:
                # Model transfer
                model_transfer_module = self.transfer_learning_orchestrator.transfer_submodules["Model_transfer"]
                if model_transfer_module is not None:
                    transferred_mapping_region_model = (self.transfer_learning_orchestrator.
                                                        transfer_submodules["Model_transfer"].
                                                        recommend_best_model(similar_experiments))
                    if transferred_mapping_region_model is not None:
                        self.predictor.update_mapping_region_model(transferred_mapping_region_model)
                        self.logger.info(f"New combination of surrogate models is recommended for this iteration: \
                                                                 {transferred_mapping_region_model.values()}")
                # Configuration transfer
                configuration_transfer_module = self.transfer_learning_orchestrator.transfer_submodules[
                    "Configuration_transfer"]
                if configuration_transfer_module is not None:
                    transferred_configurations = (
                        self.transfer_learning_orchestrator.transfer_submodules["Configuration_transfer"].
                        transfer_configurations(similar_experiments))
                    transferred_configurations = list(filter(
                        lambda tc: tc.parameters not in [mc.parameters for mc in
                                                         self.experiment.measured_configurations],
                        transferred_configurations))
                    self.logger.info(f"Identified a set of promising configurations from a similar experiment, "
                                     f"{transferred_configurations}")
                    # if few shot configuration transfer just take the best transferred config
                    if configuration_transfer_module.is_few_shot:
                        predicted_configs.append(transferred_configurations[0])
                        self.logger.info(f"Measuring the best configuration from the former experiment, "
                                         f"if it has not been measured yet: "
                                         f"{transferred_configurations[0]}")
                    # if few shot model transfer, extend the transferred model with transferred configurations,
                    # take a single config from the prediction
                    elif model_transfer_module is not None and model_transfer_module.is_few_shot:
                        extended_configuration_list = self.experiment.measured_configurations + transferred_configurations
                        temp_predicted = self.predictor.predict(extended_configuration_list)[0]
                        predicted_configs.append(temp_predicted)
                        self.logger.info("Measuring a configuration using the transferred model")
                    # regular transfer of configurations
                    else:
                        while needed_configs > 0:
                            if needed_configs - number_of_predicted_configs >= 0:
                                extended_configuration_list = self.experiment.measured_configurations + transferred_configurations
                                temp_predicted = self.predictor.predict(extended_configuration_list)
                                predicted_configs.extend(temp_predicted)
                            else:
                                extended_configuration_list = self.experiment.measured_configurations + transferred_configurations
                                temp_predicted = self.predictor.predict(extended_configuration_list)
                                predicted_configs.extend(temp_predicted[:needed_configs])
                            needed_configs -= number_of_predicted_configs
                # regular transfer of models
                if model_transfer_module is not None:
                    predicted_configs.extend(self._regular_prediction(needed_configs, number_of_predicted_configs))

        for c in predicted_configs:
            if c not in self.experiment.evaluated_configurations:
                temp_msg = f"The model predicted {c}."
                self.logger.info(temp_msg)
                configs_to_be_evaluated.append(c)
            elif len(self.experiment.measured_configurations) == self.experiment.search_space.size:
                msg = "Entire Search Space has been already evaluated. Shutting down."
                self.logger.info(msg)
                if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                    publish(exchange='stop_experiment_exchange',
                            routing_key=self.experiment.unique_id,
                            body=msg)

            else:
                sampled_config = self.predictor.predict(self.experiment.measured_configurations, True)[0]
                temp_msg = f"Predicted configuration {c} has already been evaluated. Randomly sampled {sampled_config}."
                self.logger.info(temp_msg)
                configs_to_be_evaluated.append(sampled_config)

        hierarchical_configs = []
        for c in configs_to_be_evaluated:
            self.experiment.add_evaluated_configuration_to_experiment(c)
            if c.type is Configuration.Type.PREDICTED:
                self.experiment.update_model_state(True)
            else:
                self.experiment.update_model_state(False)
            self.logger.info(temp_msg)
            c_to_send = deepcopy(c)
            if self.experiment.search_space.is_flat:
                c_to_send.parameters = self.experiment.search_space.transform_flat_parameters_to_hierarchic(
                    c.parameters)
            hierarchical_configs.append(c_to_send)
            self.sub.send('log', 'info', message=temp_msg)
            if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                publish(exchange='measure_new_configuration_exchange',
                        routing_key=self.experiment.unique_id,
                        body=json.dumps({"configuration": c_to_send.to_json()}))

        return configs_to_be_evaluated, hierarchical_configs

    def _regular_prediction(self, needed_configs: int, number_of_predicted_configs: int):
        result = []
        while needed_configs > 0:
            if needed_configs - number_of_predicted_configs >= 0:
                temp_predicted = self.predictor.predict(self.experiment.measured_configurations)
                result.extend(temp_predicted)
            else:
                temp_predicted = self.predictor.predict(self.experiment.measured_configurations)
                result.extend(temp_predicted[:needed_configs])
            needed_configs -= number_of_predicted_configs
        return result

    class _EventServiceConnection(RabbitMQConnection):
        """
        This class is responsible for listening to 2 queues.
        1. `get_new_configuration_exchange` queue for triggering configuration selection process.
        2. `stop_components` for shutting down configuration selection module (in case of BRISE Experiment termination).
        """

        def __init__(self, configuration_selection):
            """
            The function for initializing consumer thread
            :param configuration_selection: instance of ConfigurationSelection class
            """
            self.configuration_selection: ConfigurationSelection = configuration_selection
            self.experiment_id = self.configuration_selection.experiment.unique_id
            super().__init__(configuration_selection)

        def bind_and_consume(self):
            self.termination_result = self.channel.queue_declare(queue='', exclusive=True)
            self.termination_queue_name = self.termination_result.method.queue
            self.channel.queue_bind(exchange='experiment_termination_exchange',
                                    queue=self.termination_queue_name,
                                    routing_key=self.experiment_id)

            self.channel.basic_consume(queue="get_new_configuration_exchange" + self.experiment_id, auto_ack=True,
                                       on_message_callback=self.configuration_selection.send_new_configurations_to_measure)
            self.channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                       on_message_callback=self.stop)
