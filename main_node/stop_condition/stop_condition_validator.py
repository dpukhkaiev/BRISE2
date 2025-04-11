import datetime
import json
import logging
import os
import re
import threading
import time

import numexpr as ne
from tools.mongo_dao import MongoDB
from tools.rabbitmq_common_tools import RabbitMQConnection, publish


class StopConditionValidator:
    """
    Main idea is to create executable boolean math expression from the different stop conditions
    using user-defined pattern (StopConditionLogic in experiment description)
    and then execute it with numexpr (math-only functions analogue of eval)
    """
    def __init__(self, experiment_id: str, experiment_description: dict):
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

        self.experiment_id = experiment_id
        self.logger = logging.getLogger(__name__)
        self.active = True
        self.expression = experiment_description["StopCondition"]["StopConditionTriggerLogic"]["Expression"]
        self.stop_condition_states = {}

        for sc_key in experiment_description["StopCondition"]["Instance"]:
            if re.search(experiment_description["StopCondition"]["Instance"][sc_key]["Name"], self.expression):
                self.stop_condition_states[experiment_description["StopCondition"]["Instance"][sc_key]["Name"]] = False

        self.expression = self.expression.replace("or", "|").replace("and", "&")
        self.repetition_interval = datetime.timedelta(**{
            experiment_description["StopCondition"]["StopConditionTriggerLogic"]["InspectionParameters"]["TimeUnit"]:
            experiment_description["StopCondition"]["StopConditionTriggerLogic"]["InspectionParameters"]["RepetitionPeriod"]}).total_seconds()

        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.connection_thread = EventServiceConnection(self)
            self.connection_thread.start()
            self.processing_thread = threading.Thread(target=self.self_evaluation, args=())
            self.channel = self.connection_thread.channel
            self.processing_thread.start()

    def self_evaluation(self):
        """
        This function performs Search Space filling check periodically according to user-defined repetition interval.
        """
        counter = 0
        listen_interval = self.repetition_interval/10
        while self.active:
            time.sleep(listen_interval)
            counter = counter + 1
            if counter % 10 == 0:
                counter = 0
                last_experiment_state = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)
                if last_experiment_state is not None:
                    numb_of_measured_configurations = last_experiment_state["Number_of_measured_configs"]
                else:
                    numb_of_measured_configurations = 0
                    self.logger.warning(f"No Experiment state is yet available for the experiment {self.experiment_id}")
                if numb_of_measured_configurations > 0:
                    search_space_size = \
                        self.database.get_last_record_by_experiment_id("Search_space", self.experiment_id)["Search_space_size"]
                    if numb_of_measured_configurations >= search_space_size and self.active:
                        self.active = False
                        msg = "Entire Search Space was measured."
                        self.logger.info(msg)
                        publish(exchange='stop_experiment_exchange',
                                routing_key=self.experiment_id,
                                body=msg)

    def validate_conditions(self, ch, method, properties, body):
        """
        This function fills self.expression variable with validation results for corresponding
        stop conditions (boolean type). Then it just evaluates this expression.
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: json pair of stop_condition_id: stop_condition_decision
        :return: result of SC validation according to user-defined pattern.
        """
        dictionary_dump = json.loads(body.decode())
        if dictionary_dump["experiment_id"] == self.experiment_id:
            self.stop_condition_states[dictionary_dump["stop_condition_type"]] = dictionary_dump["decision"]
            result = ne.evaluate(self.expression, local_dict=self.stop_condition_states)
            if result and self.active:
                self.active = False
                msg = "Stop Condition(s) was reached."
                self.logger.info(msg)
                dictionary_dump = {"experiment_id": self.experiment_id}
                body = json.dumps(dictionary_dump)
                publish(exchange='stop_experiment_exchange',
                        routing_key=self.experiment_id,
                        body=msg)

    def stop_thread(self, ch, method, properties, body):
        """
        This function stops Stop Condition microservice.
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: empty
        """
        self.connection_thread.stop()
        self.active = False


class EventServiceConnection(RabbitMQConnection):
    """
    This class is responsible for listening 2 queues.
    1. `check_stop_condition_expression_exchange` queue for triggering StopConditionTriggerLogic expression evaluation logic.
    2. `stop_components` for shutting down Stop Condition Validator (in case of BRISE Experiment termination).
    """

    def __init__(self, stop_condition_validator: StopConditionValidator):
        """
        The function for initializing consumer thread
        :param stop_condition_validator: instance of StopConditionValidator class
        """
        self.stop_condition_validator: StopConditionValidator = stop_condition_validator
        self.experiment_id = self.stop_condition_validator.experiment_id
        super().__init__(stop_condition_validator)

    def bind_and_consume(self):
        self.termination_result = self.channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.channel.queue_bind(exchange='experiment_termination_exchange',
                                queue=self.termination_queue_name,
                                routing_key=self.experiment_id)

        self.channel.basic_consume(queue='check_stop_condition_expression_exchange' + self.experiment_id,
                                   auto_ack=True,
                                   on_message_callback=self.stop_condition_validator.validate_conditions)
        self.channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                   on_message_callback=self.stop_condition_validator.stop_thread)
