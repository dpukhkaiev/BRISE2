import numexpr as ne
import re
import json
import pika
import threading
import logging


class StopConditionValidator:
    """
    Main idea is to create executable boolean math expression from the different stop conditions
    using user-defined pattern (StopConditionLogic in experiment description)
    and then execute it with numexpr (math-only functions analogue of eval)
    """
    def __init__(self, experiment):
        self.logger = logging.getLogger(__name__)
        self.blocked = False
        self.experiment = experiment
        self.expression = self.experiment.description["StopConditionTriggerLogic"]["Expression"]
        self.stop_condition_states = {}
        for sc_index in range(0, len(self.experiment.description["StopCondition"])):
            if re.search(self.experiment.description["StopCondition"][sc_index]["Type"], self.expression):
                self.stop_condition_states[self.experiment.description["StopCondition"][sc_index]["Type"]] = False
        self.expression = self.expression.replace("or", "|").replace("and", "&")
        self.event_host = self.experiment.description["General"]["EventService"]["Address"]
        self.event_port = self.experiment.description["General"]["EventService"]["Port"]
        self.listen_thread = EventServiceConnection(self)
        self.listen_thread.start()
        try:
            result = ne.evaluate(self.expression, local_dict=self.stop_condition_states)
        except KeyError:
            temp_msg = ("ERROR! Some required in StopConditionTriggerLogic expression Stop Condition blocks were undetected. "
                                "Experiment will be stopped in a few seconds. Please, check your experiment description.")
            self.logger.exception(temp_msg)
            self.stop_experiment_due_to_failed_sc_creation()

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
        self.stop_condition_states[dictionary_dump["stop_condition_type"]] = dictionary_dump["decision"]
        result = ne.evaluate(self.expression, local_dict=self.stop_condition_states)
        if result and not self.blocked:
            self.blocked = True
            msg = "Stop Condition(s) was reached. Stopping the Experiment."
            self.logger.info(msg)
            with pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.event_host,
                                            port=self.event_port)) as connection:
                with connection.channel() as channel:
                    channel.basic_publish(exchange='',
                                                routing_key='stop_experiment_queue',
                                                body='')

    def stop_thread(self, ch, method, properties, body):
        """
        This function stops Stop Condition microservice.
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: empty
        """
        self.listen_thread.stop()
        self.thread_is_active = False

    def stop_experiment_due_to_failed_sc_creation(self):
        """
        This function sends stop_experiment message to main node. It could be triggered only if
        Stop Condition initialization fails.
        """
        with pika.BlockingConnection(
                pika.ConnectionParameters(host=self.event_host,
                                        port=self.event_port)) as connection:
            with connection.channel() as channel:
                channel.basic_publish(exchange='',
                                        routing_key='stop_experiment_queue',
                                        body="")


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
