import json
import logging
import os
import threading
import uuid

from core_entities.configuration import Configuration
from tools.mongo_dao import MongoDB
from tools.rabbitmq_common_tools import RabbitMQConnection, publish


class WSClient:

    def __init__(self, experiment_id: str):
        """
        :param experiment_id: ID of experiment, required to get experiment description from DB
        """
        # Properties that holds general task configuration (shared between task runs).
        self.logger = logging.getLogger(__name__)
        self.experiment_id = experiment_id
        database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                           os.getenv("BRISE_DATABASE_PORT"),
                           os.getenv("BRISE_DATABASE_NAME"),
                           os.getenv("BRISE_DATABASE_USER"),
                           os.getenv("BRISE_DATABASE_PASS"))

        experiment_description = None
        while experiment_description is None:
            experiment_description = database.get_last_record_by_experiment_id("Experiment_description", experiment_id)
        task_configuration = experiment_description["TaskConfiguration"]
        self._task_name = task_configuration["TaskName"]
        self.parameter_names = []
        self._objectives = task_configuration["Objectives"]
        self._scenario = task_configuration["Scenario"]
        self._time_for_one_task_running = task_configuration[
            "MaxTimeToRunTask"] if "MaxTimeToRunTask" in task_configuration else float("inf")
        # Properties that holds current task data.
        self.measurement = {}
        # Create a connection and channel for sending configurations
        self.number_of_workers_lock = threading.Lock()
        self._number_of_workers = None
        self.connection_thread = None
        self.init_connection()

    def init_connection(self):
        """
        The function creates a connection to a rabbitmq instance
        """
        # Create listeners thread
        self.connection_thread = EventServiceConnection(self)
        self.channel = self.connection_thread.channel
        self.connection_thread.start()

    ####################################################################################################################
    # Supporting methods.
    def _send_measurement(self, id_measurement, measurement):
        """
        Method to compose task description to JSON format and send it to Workers.
        :param id_measurement: ID of measurement to send
        :param measurement: measurement description
        """
        number_ready_task = len(measurement['tasks_results'])
        for i, task_parameter in enumerate(measurement['tasks_to_send']):
            if i >= number_ready_task:
                # TODO: Tasks should (1) be encapsulated as separate class, (2) and created by Configuration.
                self.logger.info("Sending task: %s" % task_parameter)
                task_description = dict()
                task_description["experiment_id"] = self.experiment_id
                task_description["id_measurement"] = id_measurement
                task_description["task_id"] = str(uuid.uuid4())
                config = Configuration.from_json(measurement["configuration"])
                task_description["experiment_id"] = config.experiment_id
                task_description["task_name"] = self._task_name
                task_description["time_for_run"] = self._time_for_one_task_running
                task_description["Scenario"] = self._scenario
                task_description["result_structure"] = self._objectives
                task_description["parameters"] = task_parameter
                publish(exchange='',
                        routing_key='task_queue',
                        body=json.dumps(task_description))

    def work(self, ch, method, properties, body) -> None:
        """
        Callback method to request from Repeater for Configuration measurement.
        Creates a new measurement, sends tasks to workers and controls the number of executed tasks.
        When the required number of Tasks is performed, reports the results back to Repeater (see _send_measurement).
        """
        dictionary_dump = json.loads(body.decode())
        j_conf = dictionary_dump["configuration"]
        tasks = dictionary_dump["tasks"]
        measurement_id = str(uuid.uuid4())
        self.measurement[measurement_id] = {}
        self.measurement[measurement_id]["tasks_to_send"] = tasks
        self.measurement[measurement_id]["tasks_results"] = []
        self.measurement[measurement_id]["configuration"] = j_conf
        self._send_measurement(measurement_id, self.measurement[measurement_id])

    def get_number_of_workers(self) -> int:
        result = self.channel.queue_declare(
            queue="task_queue",
            durable=True,
            passive=True
        )
        return result.method.consumer_count  # number of consumer for task_queue is number of workers

    def get_number_of_needed_configurations(self, ch=None, method=None, properties=None, body=None):
        """
        The function that returns the number of needed configurations for making balanced loading
        :return:
        """
        with self.number_of_workers_lock:
            current_number_of_worker = self.get_number_of_workers()
            if self._number_of_workers is None:
                self._number_of_workers = current_number_of_worker
            differences = self.get_number_of_workers() - self._number_of_workers
            self._number_of_workers = current_number_of_worker
            if differences == 0:
                worker_capacity = 1
            elif differences > 0:
                worker_capacity = differences + 1
            else:
                worker_capacity = 0
        dictionary_dump = {"worker_capacity": worker_capacity}
        body = json.dumps(dictionary_dump)
        publish(exchange='get_new_configuration_exchange',
                routing_key=self.experiment_id,
                body=body)

    def is_all_tasks_finish(self, id_measurement):
        """
        Checking are all tasks for specific configuration finish or not
        :param id_measurement: id specific measurement
        :return: True or False
        """
        if len(self.measurement[id_measurement]['tasks_results']) == len(
                self.measurement[id_measurement]['tasks_to_send']):
            return True
        else:
            return False

    def get_task_results(self, channel, method, properties, body):
        """
        Callback function for the result of tasks
        :param channel: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of a task in bytes format
        """
        task_result = json.loads(body.decode())
        try:
            self.measurement[task_result['id_measurement']]['tasks_results'].append(
                task_result['task_result'])
            # TODO: parallelization: Worker Service should not wait for entire bunch of Tasks to finish.
            # We should decouple one from another.
            if self.is_all_tasks_finish(task_result['id_measurement']):
                publish(exchange='measurement_results_exchange',
                        routing_key=self.experiment_id,
                        body=json.dumps(self.measurement[task_result['id_measurement']]))

                self.logger.debug("Results for {task_param} : {task_res}".format(
                    task_param=str(self.measurement[task_result['id_measurement']]['tasks_to_send']),
                    task_res=str(self.measurement[task_result['id_measurement']]['tasks_results'])))
                del self.measurement[task_result['id_measurement']]
        except KeyError:
            self.logger.info("The old task was received")  # in case of restart main without cleaning all queues


class EventServiceConnection(RabbitMQConnection):
    """
    This class runs WorkerService functionality in a separate thread,
    connected to the `task_result_exchange` as consumer and sends tasks results into `measurement_results_exchange`.
    """

    def __init__(self, ws_client):
        """
        The function for initializing consumer thread
        :param ws_client: WSClient instances
        """
        self.ws_client = ws_client
        self.experiment_id = self.ws_client.experiment_id
        super().__init__(ws_client)

    def bind_and_consume(self):
        self.termination_result = self.channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.channel.queue_bind(exchange='experiment_termination_exchange',
                                queue=self.termination_queue_name,
                                routing_key=self.experiment_id)
        self.channel.basic_consume(queue='task_result_exchange' + self.experiment_id, auto_ack=True,
                                   on_message_callback=self.ws_client.get_task_results)
        self.channel.basic_consume(queue='process_tasks_exchange' + self.experiment_id, auto_ack=True,
                                   on_message_callback=self.ws_client.work)
        self.channel.basic_consume(queue='get_worker_capacity_exchange' + self.experiment_id, auto_ack=True,
                                   on_message_callback=self.ws_client.get_number_of_needed_configurations)
        self.channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                   on_message_callback=self.stop)

        self.sender_lock = threading.Lock()  # only one thread can use a channel for sending message
