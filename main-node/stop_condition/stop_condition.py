import logging
import threading
import pika
import time
import datetime
import json

from abc import ABC, abstractmethod
from core_entities.experiment import Experiment

class StopCondition(ABC):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        self.experiment = experiment
        self.event_host = self.experiment.description["General"]["EventService"]["Address"]
        self.event_port = self.experiment.description["General"]["EventService"]["Port"]
        self.stop_condition_type = stop_condition_parameters["Type"]
        self.decision = False
        self.logger = logging.getLogger(stop_condition_parameters["Type"])
        self.repetition_interval = self.interval = datetime.timedelta(**{
                self.experiment.description["StopConditionTriggerLogic"]["InspectionParameters"]["TimeUnit"]: self.experiment.description["StopConditionTriggerLogic"]["InspectionParameters"]["RepetitionPeriod"]
                }).total_seconds()

    def start_threads(self):
        """
        Start 2 threads.
        One thread listens event to shut down Stop Condition.
        Second thread run the functionality of Stop Condition (`self_evaluation` method).
        """
        self.listen_thread = EventServiceConnection(self)
        self.listen_thread.start()
        self.thread_is_active = True
        self.thread = threading.Thread(target=self.self_evaluation, args=())
        self.thread.start()

    def stop_threads(self, ch, method, properties, body):
        """
        This function stops Stop Condition microservice.
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: empty
        """
        self.listen_thread.stop()
        self.thread_is_active = False

    @abstractmethod
    def is_finish(self): pass

    def update_expression(self, stop_condition_type: str, decision: bool) -> None:
        """
        This function sends event to Stop Condition Validator with command to check StopConditionTriggerLogic expression, 
        since this particular Stop Condition was triggered.
        :param stop_condition_type: Stop Condition identificator
        :param decision: Stop Condition decision (boolean)
        """
        dictionary_dump = {"stop_condition_type": stop_condition_type,
                           "decision": decision
                           }
        body = json.dumps(dictionary_dump)
        with pika.BlockingConnection(
                pika.ConnectionParameters(host=self.event_host,
                                        port=self.event_port)) as connection:
            with connection.channel() as channel:
                channel.basic_publish(exchange='',
                                        routing_key='check_stop_condition_expression_queue',
                                        body=body)

    def self_evaluation(self):
        """
        This function performs self-evaluation of Stop Condition periodically according to user-defined repetition interval.
        """
        self.counter = 0
        listen_interval = self.repetition_interval/10
        while self.thread_is_active:
            # time.sleep blocks thread execution for whole time specified in function argument
            # and stop message from main-node could be delivered only after this timer ends.
            # This code decision is designed to accelerate stopping process.   
            time.sleep(listen_interval)
            self.counter = self.counter + 1
            if self.counter == self.repetition_interval:
                self.counter = 0
                if len(self.experiment.measured_configurations) > 0:
                    self.is_finish()

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
    This class is responsible for listening `stop_brise_components` queue for shutting down Stop Condition (in case of BRISE Experiment termination).
    """

    def __init__(self, stop_condition: StopCondition):
        """
        The function for initializing consumer thread
        :param stop_condition: an instance of Stop Condition object
        """
        super(EventServiceConnection, self).__init__()
        self.stop_condition: StopCondition = stop_condition
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.stop_condition.event_host, port=self.stop_condition.event_port))
        self.consume_channel = self.connection.channel()
        self.termination_result = self.consume_channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.consume_channel.queue_bind(exchange='brise_termination_sender', queue=self.termination_queue_name)
        self._is_interrupted = False
        self.consume_channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                           on_message_callback=self.stop_condition.stop_threads)

    def stop(self):
        """
        The function for thread stop
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
