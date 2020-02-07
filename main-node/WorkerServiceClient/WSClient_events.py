import json
import pika
import pika.exceptions
import threading
import uuid
import logging
import csv

from os.path import isfile

from WorkerServiceClient.task_errors_check import error_check


class ConsumerThread(threading.Thread):
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
        super(ConsumerThread, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.ws_client = ws_client
        self._host = host
        self._port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port))

        self.consume_channel = self.connection.channel()
        self.consume_channel.basic_consume(queue='task_result_queue', auto_ack=True,
                                           on_message_callback=self.get_task_results)

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
                # TODO: parallelization: Worker Service should not wait for entire bunch of Tasks to finish.We should decouple one from another.
                if self.is_all_tasks_finish(task_result['id_measurement']):
                    try:
                        self.ws_client.dump_results_to_csv()
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

    def stop(self):
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


class WSClient:

    def __init__(self, task_configuration: dict, host: str, port: int, logfile: str):
        """
        Worker Service client, that uses pika library to communicate with rabbitmq: send task and get results
        (communication based on events).
        :param task_configuration: Dictionary. Represents "TaskConfiguration" of BRISE configuration file.
        :param host: host address of rabbitmq service
        :param port: port of rabbitmq main-service
        :param logfile: String. Path to file, where Worker Service Client will store results of each experiment.
        """
        # Properties that holds general task configuration (shared between task runs).
        self._task_name = task_configuration["TaskName"]
        self._task_parameters = task_configuration["TaskParameters"]
        self._result_structure = task_configuration["ResultStructure"]
        self._result_data_types = task_configuration["ResultDataTypes"]
        self._expected_values_range = task_configuration["ExpectedValuesRange"]
        self._scenario = task_configuration["Scenario"]
        self._time_for_one_task_running = task_configuration[
            "MaxTimeToRunTask"] if "MaxTimeToRunTask" in task_configuration else float("inf")
        self._log_file_path = logfile
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
        self.listen_thread = ConsumerThread(self.event_host, self.event_port, self)
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
                        task_description["task_name"] = self._task_name
                        task_description["time_for_run"] = self._time_for_one_task_running
                        task_description["scenario"] = self._scenario
                        task_description["result_structure"] = self._result_structure
                        task_description["params"] = {}
                        for index, parameter in enumerate(self._task_parameters):
                            task_description["params"][self._task_parameters[index]] = str(task_parameter[index])
                        try:
                            channel.basic_publish(exchange='',
                                                  routing_key='task_queue',
                                                  body=json.dumps(task_description))
                        except pika.exceptions.ChannelWrongStateError as err:
                            if not channel.is_open:
                                self.logger.warning("Attempt to send a message after closing the connection")
                            else:
                                raise err

    def _report_according_to_required_structure(self) -> list:
        results_to_report = []

        for key in self.measurement.keys():
            for task_index, one_task_result in enumerate(self.measurement[key]["tasks_results"]):
                one_task_result["ResultValidityCheckMark"] = 'OK'
                current_task = []
                current_task.extend(self.measurement[key]["tasks_to_send"][task_index])
                for index, parameter in enumerate(self._result_structure):
                    one_task_result = error_check(one_task_result, parameter, self._expected_values_range[index],
                                                  self._result_data_types[index])
                    current_task.append(one_task_result["result"][parameter])
                results_to_report.append(current_task)

        return results_to_report

    def dump_results_to_csv(self):
        try:
            file_exists = isfile(self._log_file_path)
            if not file_exists:
                # Create file and write header(legend).
                with open(self._log_file_path, 'w') as f:
                    legend = ''
                    for column_name in self._task_parameters:
                        legend += column_name + ", "
                    for column_name in self._result_structure:
                        legend += column_name + ", "
                    f.write(legend[:legend.rfind(', ')] + '\n')
            # Writing the results

            with open(self._log_file_path, 'a', newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for result in self._report_according_to_required_structure():
                    writer.writerow(result)
        except Exception as error:
            self.logger.error("Failed to write the results: %s" % error, exc_info=True)

    ####################################################################################################################
    # Outgoing interface for running measurement(s)
    def work(self, j_conf, tasks):
        """
        Prepare and send current measurement to task_queue
        :param j_conf: configuration in JSON format
        :param tasks: list of tasks
        """
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

    def get_number_of_needed_configurations(self) -> int:
        """
        The function that returns the number of needed configurations for making balanced loading
        :return:
        """
        with self.number_of_workers_lock:
            current_number_of_worker = self.get_number_of_workers()
            if self._number_of_workers is None:
                self._number_of_workers = current_number_of_worker
                return self._number_of_workers
            differences = self.get_number_of_workers() - self._number_of_workers
            self._number_of_workers = current_number_of_worker
            if differences == 0:
                return 1
            elif differences > 0:
                return differences + 1
            else:
                return 0

    def stop(self):
        self.listen_thread.stop()
        self.listen_thread.join()
