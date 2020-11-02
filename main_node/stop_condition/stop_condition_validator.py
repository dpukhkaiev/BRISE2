import datetime
import json
import logging
import os
import re
import threading
import time

import numexpr as ne
import pika
from tools.mongo_dao import MongoDB


class StopConditionValidator:
    """
    Main idea is to create executable boolean math expression from the different stop conditions
    using user-defined pattern (StopConditionLogic in experiment description)
    and then execute it with numexpr (math-only functions analogue of eval)
    """
    def __init__(self, experiment_id: str, experiment_description: dict):
        self.event_host = os.getenv("BRISE_EVENT_SERVICE_HOST")
        self.event_port = os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT")
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

        self.experiment_id = experiment_id
        self.logger = logging.getLogger(__name__)
        self.blocked = False
        self.expression = experiment_description["StopConditionTriggerLogic"]["Expression"]
        self.stop_condition_states = {}
        for sc_index in range(0, len(experiment_description["StopCondition"])):
            if re.search(experiment_description["StopCondition"][sc_index]["Name"], self.expression):
                self.stop_condition_states[experiment_description["StopCondition"][sc_index]["Name"]] = False
        self.expression = self.expression.replace("or", "|").replace("and", "&")
        self.repetition_interval = datetime.timedelta(**{
            experiment_description["StopConditionTriggerLogic"]["InspectionParameters"]["TimeUnit"]:
            experiment_description["StopConditionTriggerLogic"]["InspectionParameters"]["RepetitionPeriod"]}).total_seconds()
        self.listen_thread = EventServiceConnection(self)
        self.listen_thread.start()
        self.thread = threading.Thread(target=self.self_evaluation, args=())
        self.thread.start()

    def self_evaluation(self):
        """
        This function performs Search Space filling check periodically according to user-defined repetition interval.
        """
        counter = 0
        listen_interval = self.repetition_interval/10
        while not self.blocked:
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
                    if numb_of_measured_configurations >= search_space_size and not self.blocked:
                        self.blocked = True
                        msg = "Entire Search Space was measured."
                        self.logger.info(msg)
                        with pika.BlockingConnection(
                                pika.ConnectionParameters(host=self.event_host,
                                                          port=self.event_port)) as connection:
                            with connection.channel() as channel:
                                channel.basic_publish(exchange='',
                                                      routing_key='stop_experiment_queue',
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
            if result and not self.blocked:
                self.blocked = True
                msg = "Stop Condition(s) was reached."
                self.logger.info(msg)
                dictionary_dump = {"experiment_id": self.experiment_id}
                body = json.dumps(dictionary_dump)
                with pika.BlockingConnection(
                        pika.ConnectionParameters(host=self.event_host,
                                                  port=self.event_port)) as connection:
                    with connection.channel() as channel:
                        channel.basic_publish(exchange='',
                                              routing_key='stop_experiment_queue',
                                              body=msg)

    def stop_thread(self, ch, method, properties, body):
        """
        This function stops Stop Condition microservice.
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: empty
        """
        self.listen_thread.stop()
        self.blocked = True

class EventServiceConnection(threading.Thread):
    """
    This class is responsible for listening 2 queues.
    1. `check_stop_condition_expression_queue` queue for triggering StopConditionTriggerLogic expression evaluation logic.
    2. `stop_components` for shutting down Stop Condition Validator (in case of BRISE Experiment termination).
    """

    def __init__(self, stop_condition_validator: StopConditionValidator):
        """
        The function for initializing consumer thread
        :param stop_condition_validator: instance of StopConditionValidator class
        """
        super(EventServiceConnection, self).__init__()
        self.stop_condition_validator: StopConditionValidator = stop_condition_validator
        self._host = stop_condition_validator.event_host
        self._port = stop_condition_validator.event_port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port))
        self.consume_channel = self.connection.channel()
        self.termination_result = self.consume_channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.consume_channel.queue_bind(exchange='brise_termination_sender', queue=self.termination_queue_name)
        self._is_interrupted = False
        self.consume_channel.basic_consume(queue='check_stop_condition_expression_queue', auto_ack=True,
                                           on_message_callback=self.stop_condition_validator.validate_conditions)
        self.consume_channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                           on_message_callback=self.stop_condition_validator.stop_thread)

    def stop(self):
        """
        The function for stopping consumer thread
        """
        self._is_interrupted = True

    def run(self):
        """
        Point of entry to tasks results consumers functionality,
        listening of queue with task result
        """
        try:
            while not self._is_interrupted:
                self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
        finally:
            if self.connection.is_open:
                self.connection.close()
