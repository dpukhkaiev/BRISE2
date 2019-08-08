import socketIO_client
from math import ceil
from time import time
from os.path import isfile
import csv
import logging


class WSClient():

    def __init__(self, task_configuration, wsclient_addr, logfile):
        """
        Worker Service client, that uses socketIO_client library to communicate with Worker Service: send task and get results
        (communication based on events).
        :param task_configuration: Dictionary. Represents "TaskConfiguration" of BRISE configuration file.
        :param wsclient_addr: String. Network address of Worker Service (including port).
        :param logfile: String. Path to file, where Worker Service Client will store results of each experiment.
        """
        self.logger = logging.getLogger(__name__)
        # Creating the SocketIO object and connecting to main node namespace - "/main_node"
        self.logger.info("INFO: Connecting to the Worker Service at '%s' ..." % wsclient_addr)
        # Configuring logging for SocketIO client
        [logging.getLogger('socketIO-client').addHandler(handler) for handler in logging.getLogger().handlers]
        self.socketIO = socketIO_client.SocketIO(wsclient_addr)
        self.socketIO.define(socketIO_client.LoggingSocketIONamespace, "/main_node")

        self.servername = wsclient_addr
        # Properties that holds general task configuration (shared between task runs).
        self._exp_config = task_configuration
        self._task_name = task_configuration["TaskName"]
        self._task_parameters = task_configuration["TaskParameters"]
        self._result_structure = task_configuration["ResultStructure"]
        self._result_data_types = task_configuration["ResultDataTypes"]
        self._scenario = task_configuration["Scenario"]
        self._time_for_one_task_running = task_configuration["MaxTimeToRunTask"] if "MaxTimeToRunTask" in task_configuration else float("inf")
        self._log_file_path = logfile
        self._number_of_workers = 0
        self._got_ping_response = False

        # Properties that holds current task data.
        self.cur_tasks_ids = []
        self.current_results = []

        # Defining events that will be processed by the Worker Service Client.
        self.socketIO.on("ping_response", self.__ping_response, path="/main_node")
        self.socketIO.on("task_accepted", self.__task_accepted, path="/main_node")
        self.socketIO.on("wrong_task_structure", self.__wrong_task_structure, path="/main_node")
        self.socketIO.on("task_results", self.__task_results, path="/main_node")
        self.connect()

    def __del__(self):
        self.disconnect()

    ####################################################################################################################
    # Private methods that are reacting to the events FROM Worker Service Described below.
    # They cannot be accessed from outside of the class and manipulates task data stored inside object.
    #

    def __ping_response(self, *args):
        self.logger.info("Worker Service has {0} connected workers: {1}".format(len(args[0]), str(args[0])))
        self._number_of_workers = len(args[0])
        self._got_ping_response = True

    def __ping_ws(self):
        self._got_ping_response = False
        self.socketIO.emit('ping', path='/main_node')
        while not self._got_ping_response:
            self.socketIO.wait(0.1)

    def connect(self):
        # Verifying connection by sending "ping" event to Worker Service into main node namespace.
        # Waiting for response, if response is OK - proceed.
        self.socketIO.connect('/main_node')
        self.logger.debug("Sending 'ping' event to the Worker Service...")
        self.__ping_ws()

    def disconnect(self):
        if self.socketIO.connected:
            self.logger.debug("Disconnecting from Worker Service.")
            self._terminate_not_finished_tasks()
            self.socketIO.disconnect()

    def __task_accepted(self, ids):
        self.cur_tasks_ids = ids

    def __wrong_task_structure(self, received_task):
        self.disconnect()
        self.logger.error("Worker Service does not supports specified task structure:\n%s" % received_task)
        raise TypeError("Incorrect task structure:\n%s" % received_task)

    def __task_results(self, results):
        # This check is Workaround for non-working task termination logic on Worker Service side.
        # It could happen, that some results from previous tasks (that should be terminated) came at new run.
        if results['task id'] in self.cur_tasks_ids:
            ids_of_already_finished_tasks = [result['task id'] for result in self.current_results]
            if results['task id'] in ids_of_already_finished_tasks:
                # Workaround for floating on Worker Service.
                # It could happens that WorkerService assigns one task on multiple workers.
                self.logger.warning("Warning - Worker Server reported same task results multiple times!"
                                    "(Task were running on multiple Worker nodes)")
            else:
                self.current_results.append(results)

    def _prepare(self):
        self.cur_tasks_ids = []
        self.current_results = []
        if not self.socketIO.connected:
            self.connect()

    ####################################################################################################################
    # Supporting methods.
    def _send_task(self, tasks_parameters):
        self.logger.info("Sending task: %s" % tasks_parameters)
        tasks_to_send = []

        for task_parameter in tasks_parameters:
            task_description = dict()
            task_description["task_name"] = self._task_name
            task_description["scenario"] = self._scenario
            task_description["params"] = {}
            for index, parameter in enumerate(self._task_parameters):
                task_description["params"][parameter] = str(task_parameter[index])
            tasks_to_send.append(task_description)

        self.socketIO.emit('add_tasks', tasks_to_send, path='/main_node')  # response - task_accepted or wrong_task_structure

    def _terminate_not_finished_tasks(self):
        if self.cur_tasks_ids:
            termination_candidates = self.cur_tasks_ids.copy()
            for result in self.current_results:
                termination_candidates.remove(result["task id"])
            if termination_candidates:
                self.logger.debug("Terminating unfinished Tasks.")
                self.socketIO.emit("terminate_tasks", termination_candidates, path='/main_node')

    def _report_according_to_required_structure(self):
        results_to_report = []
        for one_task_result in self.current_results:
            current_task = []
            for index, parameter in enumerate(self._result_structure):
                if self._result_data_types[index] == 'str':
                    current_task.append(one_task_result["result"][parameter])
                    continue
                current_task.append(eval("{datatype}({value})".format(datatype=self._result_data_types[index],
                                                                      value=one_task_result["result"][parameter])))
            results_to_report.append(current_task)
        return results_to_report

    def _dump_results_to_csv(self):
        try:
            file_exists = isfile(self._log_file_path)
            if not file_exists:
                # Create file and write header(legend).
                with open(self._log_file_path, 'w') as f:
                    legend = ''
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
    # Outgoing interface for running task(s)
    def work(self, task):
        """
        Prepare and send current task to Worker Service, wait for results, terminate stragglers, report all results back.

        :param task: list of configurations (tasks), e.g. [[123.5, 12, 'normal'], [165, 2, 'linear']...] The structure
        of each task should correspond specified structure in experiments_configuration["TaskParameters"].

        :return: List with result of running all the experiments. First, each experiment will have a structure,
        specified in the experiments_configuration["TaskParameters"], next all values will be casted to data types,
        specified in the experiments_configuration["ResultDataTypes"].
        """
        self._prepare()
        self._send_task(task)

        #   Start waiting for result.
        #   max_given_time_to_run_all_tasks - time to run all current experiments(tasks) on
        #   all currently available workers(monitored by 'ping_response' event).
        #
        #   E.g. we have 7 tasks for 3 workers. Each experiment should run not more than
        #   5 seconds (specified in self._time_for_one_task_running). Resulting value will be 15 seconds.
        #   If the tasks were not finished at 15 seconds time interval, they will be terminated.
        try:
            waiting_started = time()
            # BUG Throw the Error if no workers at all. Division by zero
            max_given_time_to_run_all_tasks = ceil(
                len(task) / self._number_of_workers) * self._time_for_one_task_running
            while time() - waiting_started < max_given_time_to_run_all_tasks:
                self.socketIO.wait(0.2)
                if len(self.current_results) >= len(self.cur_tasks_ids):
                    break

            if len(self.current_results) < len(self.cur_tasks_ids):
                raise TimeoutError("Not all Task have been finished in time.")
            else:
                self.logger.info(
                    "All tasks (%s) finished after %s seconds. " % (len(task), round(time() - waiting_started)))
                self.logger.info("Results: %s" % str(self._report_according_to_required_structure()))
                return self.current_results
        except Exception as e:
            self.logger.error("Unable finish Tasks. Reporting what had got: %s" %
                              str(self._report_according_to_required_structure()), exc_info=e)
            return self.current_results
        finally:
            self._dump_results_to_csv()
            self._terminate_not_finished_tasks()

    def get_number_of_workers(self):
        self.__ping_ws()
        return self._number_of_workers


# A small unit test. Worker service should already run on port 49153 and has a resolving domain name "w_service".
if __name__ == "__main__":
    wsclient = 'w_service:49153'
    config = {
        "TaskName": "energy_consumption",
        "Scenario": {
            "ws_file": "Radix-500mio.csv"
        },
        "TaskParameters": ["frequency", "threads"],
        "ResultStructure": ["energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "Type": "student_deviation",
        "MaxTasksPerConfiguration": 10,
        "MaxTimeToRunTask": 10
    }
    task_data = [[2900.0, 32], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16],
                 [1800.0, 16], [1800.0, 16]]
    from random import randint
    from time import sleep

    client = WSClient(config, wsclient, 'TEST_WSClient_results.csv')
    for x in range(30):
        tasks = task_data[:randint(0, len(task_data))]
        result1 = client.work(tasks)
        sleep(4)
