import logging
import json

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from configuration_selection.model.predictor import Predictor
from tools.front_API import API
from tools.rabbitmq_common_tools import RabbitMQConnection, publish
from transfer_learning.transfer_learning_module import TransferLearningModule

from collections import OrderedDict


class ConfigurationSelection:
    """
    Orchestration class for Configuration Selection module.
    """

    def __init__(self, experiment: Experiment):
        self.sub = API()
        self.experiment = experiment
        self.experiment_id = self.experiment.unique_id
        # TODO: information, related to experiment, such as ED, UUID, etc. could be encapsulated into `context` entity.
        self.predictor: Predictor = Predictor(
            self.experiment_id, self.experiment.description, self.experiment.search_space
        )
        # Initialize Transfer Learning module
        if self.experiment.description["TransferLearning"]["isEnabled"]:
            self.is_transfer_enabled = True
            self.tl_module = TransferLearningModule(self.experiment.description, self.experiment_id)
        self.logger = logging.getLogger(__name__)
        self.connection_thread = EventServiceConnection(self)
        self.connection_thread.start()

    def send_new_configurations_to_measure(self, ch, method, properties, body):
        """
        This callback function will be triggered on arrival of ONE measured Configuration.
        When there is new measured Configuration, following steps should be done:

            -   update and validate models;

            -   pick either by model, or by selection algorithm new Configuration(s) for evaluation;
                Note: The amount of new Configurations are:
                - 0 if number of available Worker nodes decreased;
                - 1 if number of available Workers did not change;
                - N + 1 if number of available Worker increased by N;

            -   send new Configuration to Repeater for evaluation.
        """

        needed_configs = json.loads(body.decode()).get("worker_capacity", 1)
        for _ in range(needed_configs):
            # TODO some of parameters could be predicted, other could be sampled, need to change Configuration.Type
            # TODO: check the logic. Now, if TL is disabled, prediction takes place sa usual.
            # If enabled - n points are sampled deterministically.
            # Possible consequences - only exps. with used TL can be further used for TL
            if not self.is_transfer_enabled:
                config = self.predictor.predict(self.experiment.measured_configurations)
            else:
                if len(self.experiment.measured_configurations) > \
                        self.experiment.description["TransferLearning"]["TransferExpediencyDetermination"]["MinNumberOfSamples"]:
                    transferred_knowledge = self.tl_module.get_transferred_knowledge()
                    recommended_models = transferred_knowledge["Recommended_models"]
                    transferred_models = transferred_knowledge["Models_to_transfer"]
                    transferred_best_configuration = transferred_knowledge["Best_configuration_to_transfer"]
                    transferred_configurations = transferred_knowledge["Configurations_to_transfer"]
                    if recommended_models is not None and recommended_models != self.predictor.predictor_config["models"]:
                        self.predictor.predictor_config["models"] = recommended_models
                        self.predictor.models_dumps = [None] * len(recommended_models)
                        self.logger.info(f"New combination of surrogate models is recommended for this iteration: \
                                          {recommended_models}")
                    if transferred_best_configuration is not None:
                        config = transferred_best_configuration
                        self.logger.info(f"Trying to measure best configuration from former experiment, \
                                         if it was not measured yet: {config}")
                    else:
                        if transferred_models is not None and len(transferred_models) > 0:
                            config = self.predictor.predict(self.experiment.measured_configurations,
                                                            transferred_models=transferred_models)
                            config.type = Configuration.Type.TRANSFERRED
                            self.logger.info(f"A combination of old surrogates will be used on this iteration: \
                                             {transferred_models}")
                        else:
                            config = self.predictor.predict(self.experiment.measured_configurations,
                                                            transferred_configurations=transferred_configurations)
                        if transferred_configurations is not None:
                            if len(transferred_configurations) > 0:
                                config.type = Configuration.Type.TRANSFERRED
                        elif recommended_models is not None:
                                config.type = Configuration.Type.TRANSFERRED
                else:
                    new_parameter_values = OrderedDict()
                    while not self.experiment.search_space.validate(new_parameter_values, is_recursive=True):
                        self.experiment.search_space.generate(new_parameter_values)
                    config = Configuration(
                        new_parameter_values, Configuration.Type.FROM_SELECTOR, self.experiment_id
                    )

            if config not in self.experiment.evaluated_configurations:
                temp_msg = f"Model predicted {config}."
            else:
                while config in self.experiment.evaluated_configurations:
                    if len(self.experiment.evaluated_configurations) >= self.experiment.search_space.get_size():
                        msg = "Entire Search Space was evaluated. Shutting down."
                        self.logger.warning(msg)
                        publish(exchange='stop_experiment_exchange',
                                routing_key=self.experiment_id,
                                body=msg)
                        break

                    new_parameter_values = OrderedDict()
                    while not self.experiment.search_space.validate(new_parameter_values, is_recursive=True):
                        self.experiment.search_space.generate(new_parameter_values)
                    config = Configuration(
                        new_parameter_values, Configuration.Type.FROM_SELECTOR, self.experiment_id
                    )
                temp_msg = f"Fully randomly sampled {config}."
            self.experiment.add_evaluated_configuration_to_experiment(config)
            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)
            publish(exchange='measure_new_configuration_exchange',
                    routing_key=self.experiment_id,
                    body=json.dumps({"configuration": config.to_json()}))


class EventServiceConnection(RabbitMQConnection):
    """
    This class is responsible for listening 2 queues.
    1. `get_new_configuration_exchange` queue for triggering configuration selection process.
    2. `stop_components` for shutting down configuration selection module (in case of BRISE Experiment termination).
    """

    def __init__(self, configuration_selection: ConfigurationSelection):
        """
        The function for initializing consumer thread
        :param configuration_selection: instance of ConfigurationSelection class
        """
        self.configuration_selection: ConfigurationSelection = configuration_selection
        self.experiment_id = self.configuration_selection.experiment_id
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
