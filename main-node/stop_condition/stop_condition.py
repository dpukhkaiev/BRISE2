import logging
import os
import threading
import pika
import time
import datetime
import json
import os

from abc import ABC, abstractmethod
from tools.mongo_dao import MongoDB


class StopCondition(ABC):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        self.event_host = os.getenv("BRISE_EVENT_SERVICE_HOST")
        self.event_port = os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT")
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"), 
                        os.getenv("BRISE_DATABASE_PORT"), 
                        os.getenv("BRISE_DATABASE_NAME"),
                        os.getenv("BRISE_DATABASE_USER"),
                        os.getenv("BRISE_DATABASE_PASS"))

        self.experiment_id = experiment_id
        self.stop_condition_type = stop_condition_parameters["Name"]
        self.decision = False
        self.logger = logging.getLogger(stop_condition_parameters["Name"])
        self.repetition_interval = datetime.timedelta(**{
                experiment_description["StopConditionTriggerLogic"]["InspectionParameters"]["TimeUnit"]: 
                experiment_description["StopConditionTriggerLogic"]["InspectionParameters"]["RepetitionPeriod"]
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
    def is_finish(self):
        """
        Main logic of Stop Condition should be overridden in this method.
        Later, this method will be called in `self_evaluation` method with defined in Experiment Description period.

        When the Stop Condition is triggered to stop BRISE,
        it changes internal state of variable 'self.decision' to True.
        :return: None
        """
        pass

    def update_expression(self, stop_condition_type: str, decision: bool) -> None:
        """
        This function sends event to Stop Condition Validator with command to check StopConditionTriggerLogic expression, 
        since this particular Stop Condition was triggered.
        :param stop_condition_type: Stop Condition identificator
        :param decision: Stop Condition decision (boolean)
        """
        dictionary_dump = {"experiment_id": self.experiment_id,
                            "stop_condition_type": stop_condition_type,
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
        counter = 0
        listen_interval = self.repetition_interval/10
        previous_decision = self.decision   # for sending the update only when decision changes
        while self.thread_is_active:
            # time.sleep blocks thread execution for whole time specified in function argument
            # and stop message from main-node could be delivered only after this timer ends.
            # This code decision is designed to accelerate stopping process.   
            time.sleep(listen_interval)
            counter = counter + 1
            if counter % 10 == 0:
                counter = 0
                numb_of_measured_configurations = 0
                try:
                    numb_of_measured_configurations = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_measured_configs"]
                except TypeError:
                    self.logger.warning(f"No Experiment state is yet available for the experiment {self.experiment_id}")    
                if numb_of_measured_configurations > 0:
                    search_space_size = self.database.get_last_record_by_experiment_id("Search_space", self.experiment_id)["Search_space_size"]
                    if numb_of_measured_configurations >= search_space_size:
                        break
                    self.is_finish()
                    if previous_decision != self.decision:
                        msg = f"{self.__class__.__name__} Stop Condition decision: " \
                              f"{ 'stop' if self.decision else 'continue'} running Experiment."
                        self.logger.info(msg)
                        previous_decision = self.decision
                        self.update_expression(self.stop_condition_type, self.decision)

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
