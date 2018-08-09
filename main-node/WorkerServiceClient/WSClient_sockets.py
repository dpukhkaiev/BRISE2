from socketIO_client import SocketIO, BaseNamespace
from math import ceil
from time import time
from os.path import isfile
import csv
# import logging
# logging.getLogger("socketIO-client").setLevel(logging.DEBUG)
# logging.basicConfig()


class WSClient(SocketIO):

    def __init__(self, experiments_configuration, wsclient_addr, logfile):
        # Creating the SocketIO object and connecting to main node namespace - "/main_node"
        super().__init__(wsclient_addr)
        self.ws_namespace = self.define(BaseNamespace, "/main_node")

        # Properties that holds general task configuration (shared between task runs).
        self._exp_config = experiments_configuration
        self._task_name = experiments_configuration["TaskName"]
        self._task_parameters = experiments_configuration["TaskParameters"]
        self._result_structure = experiments_configuration["ResultStructure"]
        self._result_data_types = experiments_configuration["ResultDataTypes"]
        self._worker_config = experiments_configuration["WorkerConfiguration"]
        self._time_for_one_task_running = experiments_configuration["MaxTimeToRunExperiment"]
        self._log_file_path = logfile

        # Properties that holds current task data.
        self.cur_tasks_ids = []
        self.current_results = []

        # Defining events that will be processed by the Worker Service Client.
        self.ws_namespace.on("connect", self.__reconnect)
        self.ws_namespace.on("ping_response", self.__ping_response)
        self.ws_namespace.on("task_accepted", self.__task_accepted)
        self.ws_namespace.on("wrong_task_structure", self.__wrong_task_structure)
        self.ws_namespace.on("task_results", self.__task_results)

        # Verifying connection by sending "ping" event to Worker Service into main node namespace.
        # Waiting for response, if response is OK - proceed.
        self._connection_ok = False
        while not self._connection_ok:
            self.ws_namespace.emit('ping')
            self.wait(1)

    ####################################################################################################################
    # Private methods that are reacting to the events FROM Worker Service Described below.
    # They cannot be accessed from outside of the class and manipulates task data stored inside object.
    #
    def __reconnect(self):
        print("Worker Service has been connected!")

    def __ping_response(self, *args):
        print("Worker Service have {0} connected workers: {1}".format(len(args[0]), str(args[0])))
        self._connection_ok = True
        self._number_of_workers = len(args[0])

    def __task_accepted(self, ids):
        self.cur_tasks_ids = ids

    def __wrong_task_structure(self, received_task):
        self.ws_namespace.disconnect()
        self.disconnect()
        raise TypeError("Incorrect task structure:\n%s" % received_task)

    def __task_results(self, results):
        # This check is Workaround for non-working task termination logic on Worker Service side.
        # It could happen, that some results from previous tasks (that should be terminated) came at new run.
        if results['task id'] in self.cur_tasks_ids:
            ids_of_already_finished_tasks = [result['task id'] for result in self.current_results]
            if results['task id'] in ids_of_already_finished_tasks:
                # Workaround for floating on Worker Service.
                # It could happens that WorkerService assigns one task on multiple workers.
                print("Warning - Worker Server reported same task results multiple times!")
            else:
                self.current_results.append(results)

    def __perform_cleanup(self):
        self.cur_tasks_ids = []
        self.current_results = []

    ####################################################################################################################
    # Supporting methods.
    def _send_task(self, tasks_parameters):
        print("Sending task: %s" % tasks_parameters)
        tasks_to_send = []

        for task_parameter in tasks_parameters:
            task_description = dict()
            task_description["task_name"] = self._task_name
            task_description["worker_config"] = self._worker_config
            task_description["params"] = {}
            for index, parameter in enumerate(self._task_parameters):
                task_description["params"][parameter] = str(task_parameter[index])

            tasks_to_send.append(task_description)

        self.ws_namespace.emit('add_tasks', tasks_to_send)  # response - task_accepted or wrong_task_structure
        self.wait(0.2)    # wait to get back task IDs

    def _terminate_not_finished_tasks(self):
        termination_candidates = self.cur_tasks_ids
        for result in self.current_results:
            termination_candidates.remove(result["task id"])
        self.ws_namespace.emit("terminate_tasks", termination_candidates)

    def _report_according_to_required_structure(self):
        results_to_report = []
        for one_task_result in self.current_results:
            current_task = []
            for index, parameter in enumerate(self._result_structure):
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
        except Exception as e:
            print("Failed to write the results: %s" % e)

    ####################################################################################################################
    # Outgoing interface for running task(s)
    def work(self, task):
        self.__perform_cleanup()
        self._send_task(task)

        # Start waiting for results
        waiting_started = time()
        max_given_time_to_run_all_tasks = ceil(len(task) / self._number_of_workers) * self._time_for_one_task_running
        while time() - waiting_started < max_given_time_to_run_all_tasks:
            self.wait(0.5)
            if len(self.current_results) >= len(self.cur_tasks_ids):
                break

        if len(self.current_results) < len(self.cur_tasks_ids):
            print("Results were not got in time. Terminating currently running tasks.", end="")
            self._terminate_not_finished_tasks()
        else:
            print("All tasks (%s) finished after %s seconds. " % (len(task), round(time() - waiting_started)), end='')
        print("Results: %s" % str(self._report_according_to_required_structure()))
        self._dump_results_to_csv()
        return self._report_according_to_required_structure()

if __name__ == "__main__":
    wsclient = 'w_service:80'
    config = {
        "TaskName"          : "energy_consumption",
        "WorkerConfiguration": {
            "ws_file": "Radix-500mio.csv"
        },
        "TaskParameters"   : ["frequency", "threads"],
        "ResultStructure"   : ["frequency", "threads", "energy"],
        "ResultDataTypes"  : ["float", "int", "float"],
        "RepeaterDecisionFunction"  : "student_deviation",
        "MaxRepeatsOfExperiment": 10,
        "MaxTimeToRunExperiment": 10
    }
    task_data = [[2900.0, 32], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16], [1800.0, 16]]
    from random import randint
    from time import sleep
    client = WSClient(config, wsclient, 'TEST_WSClient_results.csv')
    for x in range(30):
        client.work(task_data[:randint(0, len(task_data))])
        sleep(4)
