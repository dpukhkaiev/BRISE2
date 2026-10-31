import logging
import json
import os
import threading
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

    # Upper bound on random resamples used to break a duplicate proposal within
    # a single wave before the point is skipped (see send_new_configurations_to_measure).
    _MAX_RESAMPLE_ATTEMPTS = 20

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

        # Serializes one wave of selection at a time. With batched/hybrid
        # distribution a wave is already published by a single thread and waves
        # cannot overlap (the barrier/gate holds the next wave until the current
        # batch returns), so this lock is uncontended today. It guards the
        # read-modify-write of Experiment state (evaluated/measured configurations
        # and model updates) against a future asynchronous-update path that would
        # let results — and therefore selection — overlap.
        self._selection_lock = threading.Lock()

        # Called with (published_count, wave_token) once a wave is dispatched; set
        # by the core when Racing owns the loop (MainThread).
        self.wave_dispatched_callback = None

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
        wave = json.loads(body.decode())
        needed_configs = wave.get("worker_capacity", 1)
        # Set by the Racing layer: the budget the whole wave is measured with.
        # Without it the repeater falls back to its global task count.
        task_budget = wave.get("task_budget")
        # Dates the rung, so the strategy recognises a late dispatch report as stale.
        wave_token = wave.get("wave_token")
        requested_configs = needed_configs

        predicted_configs = []
        configs_to_be_evaluated = []

        if not self.transfer_is_enabled:
            predicted_configs.extend(self._regular_prediction(needed_configs))
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
                predicted_configs.extend(self._regular_prediction(needed_configs))
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
                    offered_configurations = (
                        self.transfer_learning_orchestrator.transfer_submodules["Configuration_transfer"].
                        transfer_configurations(similar_experiments))
                    # filter out configurations the target experiment has already measured
                    measured_parameters = [mc.parameters for mc in self.experiment.measured_configurations]
                    transferred_configurations = [
                        tc for tc in offered_configurations if tc.parameters not in measured_parameters]
                    # the module had something to offer, but all of it is already measured
                    source_exhausted = len(offered_configurations) > 0 and len(transferred_configurations) == 0
                    if source_exhausted and model_transfer_module is None:
                        if configuration_transfer_module.is_few_shot:
                            # few-shot has fired; it will never offer anything again, whatever TED returns
                            experiments_to_ban = [e["Exp_unique_ID"] for e in similar_experiments]
                        else:
                            # ban only the sources that can no longer contribute anything unmeasured
                            experiments_to_ban = [e["Exp_unique_ID"] for e in similar_experiments
                                                  if all(s["parameters"] in measured_parameters
                                                         for s in e.get("Samples", []))]
                        self.transfer_learning_orchestrator.ted_module.ban_experiments(experiments_to_ban)
                    if len(transferred_configurations) > 0:
                        self.logger.info(f"Identified a set of promising configurations from a similar experiment, "
                                        f"{transferred_configurations}")
                    # a fallback is only needed when no other branch would produce a configuration
                    elif model_transfer_module is None and configuration_transfer_module.is_few_shot:
                        self.logger.info("No promising configurations were identified! Regular prediction...")
                        predicted_configs.extend(self._regular_prediction(needed_configs))
                    # if few shot configuration transfer just take the best transferred config
                    if configuration_transfer_module.is_few_shot:
                        if len(transferred_configurations) > 0:
                            predicted_configs.append(transferred_configurations[0])
                            needed_configs -= 1
                            self.logger.info(f"Measuring the best configuration from the former experiment, "
                                             f"if it has not been measured yet: "
                                             f"{transferred_configurations[0]}")
                    # if few shot model transfer, extend the transferred model with transferred configurations,
                    # take a single config from the prediction
                    elif model_transfer_module is not None and model_transfer_module.is_few_shot:
                        extended_configuration_list = self.experiment.measured_configurations + transferred_configurations
                        temp_predicted = self.predictor.predict(extended_configuration_list)[0]
                        predicted_configs.append(temp_predicted)
                        needed_configs -= 1
                        self.logger.info("Measuring a configuration using the transferred model")
                    # regular transfer of configurations
                    else:
                        extended_configuration_list = self.experiment.measured_configurations + transferred_configurations
                        while needed_configs > 0:
                            temp_predicted = self.predictor.predict(extended_configuration_list)
                            if not temp_predicted:
                                break
                            predicted_configs.extend(temp_predicted[:needed_configs])
                            needed_configs -= len(temp_predicted)
                # regular transfer of models
                if model_transfer_module is not None:
                    predicted_configs.extend(self._regular_prediction(needed_configs))

        # De-duplicate the (possibly N) predicted points against already-evaluated
        # configurations AND against the points already chosen in this wave, then
        # register them atomically, so a wave's points are checked-then-added as
        # one critical section. With N > 1 a single wave calls the predictor
        # several times on the same measured data, so a deterministic surrogate
        # can propose the same point twice within one wave; without the in-wave
        # check those duplicates would each be dispatched for measurement. Each
        # point is handled independently, so a wave may yield fewer than N configs
        # when the space is nearly exhausted (duplicates trigger a resample, or a
        # stop when the whole search space is already measured).
        with self._selection_lock:
            def _already_selected(candidate: Configuration) -> bool:
                # A candidate is a duplicate if it was measured in a previous wave
                # or has already been chosen earlier in the current wave.
                return (candidate in self.experiment.evaluated_configurations
                        or candidate in configs_to_be_evaluated)

            for c in predicted_configs:
                if not _already_selected(c):
                    temp_msg = f"The model predicted {c}."
                    self.logger.info(temp_msg)
                    configs_to_be_evaluated.append(c)
                elif len(self.experiment.measured_configurations) >= self.experiment.search_space.size:
                    # The wave is abandoned: the remaining points could only be
                    # duplicates too, and a stop must be requested exactly once.
                    msg = "Entire Search Space has been already evaluated. Shutting down."
                    self.logger.info(msg)
                    if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                        publish(exchange='stop_experiment_exchange',
                                routing_key=self.experiment.unique_id,
                                body=msg)
                    break
                else:
                    # Resample a configuration that is distinct from everything
                    # already evaluated and everything already chosen in this
                    # wave. Bounded retries so a nearly-exhausted space cannot
                    # spin forever; if no distinct point is found the point is
                    # skipped and the wave simply returns fewer than N configs.
                    sampled_config = None
                    for _ in range(self._MAX_RESAMPLE_ATTEMPTS):
                        candidate = self.predictor.predict(self.experiment.measured_configurations, True)[0]
                        if not _already_selected(candidate):
                            sampled_config = candidate
                            break
                    if sampled_config is None:
                        temp_msg = (f"Predicted configuration {c} has already been evaluated and no distinct "
                                    f"configuration could be sampled in {self._MAX_RESAMPLE_ATTEMPTS} attempts; "
                                    f"skipping this point for the current wave.")
                        self.logger.info(temp_msg)
                        continue
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
                dispatch_msg = f"Sending configuration {c} to be measured."
                self.logger.info(dispatch_msg)
                c_to_send = deepcopy(c)
                c_to_send.task_budget = task_budget
                c_to_send.rung_token = wave_token
                if self.experiment.search_space.is_flat:
                    c_to_send.parameters = self.experiment.search_space.transform_flat_parameters_to_hierarchic(
                        c.parameters)
                hierarchical_configs.append(c_to_send)
                self.sub.send('log', 'info', message=dispatch_msg)
                if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                    publish(exchange='measure_new_configuration_exchange',
                            routing_key=self.experiment.unique_id,
                            body=json.dumps({"configuration": c_to_send.to_json()}))

        if len(configs_to_be_evaluated) < requested_configs:
            self.logger.warning(f"Wave requested {requested_configs} Configuration(s) but only "
                                f"{len(configs_to_be_evaluated)} distinct one(s) could be proposed.")

        # Always report: a barrier cannot tell a still-publishing wave from a
        # finished one that came up short.
        self._report_dispatched(len(configs_to_be_evaluated), wave_token)

        return configs_to_be_evaluated, hierarchical_configs

    def _report_dispatched(self, number_of_configurations: int, wave_token) -> None:
        """
        Tell the core how many Configurations this wave really published. The wave
        is already on its way, so a broken listener must not take this thread down.
        """
        if self.wave_dispatched_callback is None:
            return
        try:
            self.wave_dispatched_callback(number_of_configurations, wave_token)
        except Exception:
            self.logger.exception(f"Failed to report a dispatched wave of "
                                  f"{number_of_configurations} Configuration(s).")

    def _regular_prediction(self, needed_configs: int) -> List[Configuration]:
        """
        Propose configurations until the wave is filled. A proposal usually yields
        NumberOfPoints configurations, but the count is taken from the proposal
        itself, as a level that has to sample cannot always serve that many.
        """
        result = []
        while len(result) < needed_configs:
            temp_predicted = self.predictor.predict(self.experiment.measured_configurations)
            if not temp_predicted:
                break
            result.extend(temp_predicted)
        return result[:needed_configs]

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
            
