import json
import logging
import threading
import uuid

import pika
import pika.exceptions
from core_entities.configuration import Configuration


class WSClient:

    def __init__(self, task_configuration: dict, host: str, port: int):
        """
        Worker Service client, that uses pika library to communicate with rabbitmq: send task and get results
        (communication based on events).
        :param task_configuration: Dictionary. Represents "TaskConfiguration" of BRISE configuration file.
        :param host: host address of rabbitmq service
        :param port: port of rabbitmq main-service
        """
        # Properties that holds general task configuration (shared between task runs).
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
        self.logger = logging.getLogger(__name__)
        self.event_host = host
        self.event_port = port
        self.listen_thread = None
        self.init_connection()

    def init_connection(self):
        """
        The function creates a connection to a rabbitmq instance
        :param host: host address of rabbitmq service
        :param port: port of rabbitmq main-service
        :return:
        """
        self.logger.info(f"Connecting to the Worker Service at {self.event_host}:{self.event_port} ...")
        # Create listeners thread
        self.listen_thread = EventServiceConnection(self.event_host, self.event_port, self)
        self.listen_thread.start()

    ####################################################################################################################
    # Supporting methods.
    def _send_measurement(self, id_measurement, measurement):
        with pika.BlockingConnection(pika.ConnectionParameters(self.event_host, self.event_port)) as connection:
            with connection.channel() as channel:
                number_ready_task = len(measurement['tasks_results'])
                for i, task_parameter in enumerate(measurement['tasks_to_send']):
                    if i >= number_ready_task:
                        self.logger.info("Sending task: %s" % task_parameter)
                        task_description = dict()
                        task_description["id_measurement"] = id_measurement
                        task_description["task_id"] = str(uuid.uuid4())
                        config = Configuration.from_json(measurement["configuration"])
                        task_description["experiment_id"] = config.experiment_id
                        task_description["task_name"] = self._task_name
                        task_description["time_for_run"] = self._time_for_one_task_running
                        task_description["Scenario"] = self._scenario
                        task_description["result_structure"] = self._objectives
                        task_description["parameters"] = task_parameter
                        try:
                            channel.basic_publish(exchange='',
                                                  routing_key='task_queue',
                                                  body=json.dumps(task_description))
                        except pika.exceptions.ChannelWrongStateError as err:
                            if not channel.is_open:
                                self.logger.warning("Attempt to send a message after closing the connection")
                            else:
                                raise err

    ####################################################################################################################
    # Outgoing interface for running measurement(s)
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
        with pika.BlockingConnection(pika.ConnectionParameters(self.event_host, self.event_port)) as connection:
            with connection.channel() as channel:
                result = channel.queue_declare(
                    queue="task_queue",
                    durable=True,
                    exclusive=False,
                    auto_delete=False,
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
        with pika.BlockingConnection(pika.ConnectionParameters(self.event_host, self.event_port)) as connection:
            with connection.channel() as channel:
                channel.basic_publish(exchange='', routing_key='get_new_configuration_queue', body=body)

    def stop(self):
        self.listen_thread.stop()
        self.listen_thread.join()


class EventServiceConnection(threading.Thread):
    """
    This class runs WorkerService functionality in a separate thread,
    connected to the `task_result_queue` as consumer and sends tasks results into `measurement_results_queue`.
    """

    def __init__(self, host, port, ws_client):
        """
        The function for initializing consumer thread
        :param host: ip address of rabbitmq service
        :param port: port of rabbitmq main-service
        :param ws_client: WSClient instances
        """
        super(EventServiceConnection, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.ws_client = ws_client
        self._host = host
        self._port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port))

        self.consume_channel = self.connection.channel()
        self.termination_result = self.consume_channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.consume_channel.queue_bind(exchange='brise_termination_sender', queue=self.termination_queue_name)
        self.consume_channel.basic_consume(queue='task_result_queue', auto_ack=True,
                                           on_message_callback=self.get_task_results)
        self.consume_channel.basic_consume(queue='process_tasks_queue', auto_ack=True,
                                           on_message_callback=self.ws_client.work)
        self.consume_channel.basic_consume(queue='get_worker_capacity_queue', auto_ack=True,
                                           on_message_callback=self.ws_client.get_number_of_needed_configurations)
        self.consume_channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                           on_message_callback=self.stop)

        self._is_interrupted = False
        self.sender_lock = threading.Lock()  # only one thread can use a channel for sending message

    def is_all_tasks_finish(self, id_measurement):
        """
        Checking are all tasks for specific configuration finish or not
        :param id_measurement: id specific measurement
        :return: True or False
        """
        if len(self.ws_client.measurement[id_measurement]['tasks_results']) == len(
                self.ws_client.measurement[id_measurement]['tasks_to_send']):
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
            self.ws_client.measurement[task_result['id_measurement']]['tasks_results'].append(
                task_result['task_result'])
            with self.connection.channel() as channel:
                if self.is_all_tasks_finish(task_result['id_measurement']):
                    try:
                        channel.basic_publish(exchange='',
                                              routing_key='measurement_results_queue',
                                              body=json.dumps(
                                                  self.ws_client.measurement[task_result['id_measurement']]))
                    except pika.exceptions.ChannelWrongStateError as err:
                        if not channel.is_open:
                            self.logger.warning("Attempt to send a message after closing the connection")
                        else:
                            raise err
                    self.logger.debug("Results for {task_param} : {task_res}".format(
                        task_param=str(self.ws_client.measurement[task_result['id_measurement']]['tasks_to_send']),
                        task_res=str(self.ws_client.measurement[task_result['id_measurement']]['tasks_results'])))
                    del self.ws_client.measurement[task_result['id_measurement']]
        except KeyError:
            self.logger.info("The old task was received")  # in case of restart main without cleaning all queues

    def stop(self, ch=None, method=None, properties=None, body=None):
        """
        The function for stop WS_client thread
        """
        self._is_interrupted = True

    def run(self):
        """
        Point of entry to tasks results consumers functionality,
        listening of queue with task result
        """
        try:
            while self.consume_channel._consumer_infos:
                self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
                if self._is_interrupted:
                    if self.connection.is_open:
                        self.connection.close()
                    break
        finally:
            if self.connection.is_open:
                self.connection.close()
