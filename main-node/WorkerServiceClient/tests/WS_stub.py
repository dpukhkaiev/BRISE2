import csv
import logging
from random import choice

from WorkerServiceClient.WSClient_sockets import WSClient


class WSClient_Stub(WSClient):
    def __init__(self, *args, **kwargs):
        """
        Worker Service client stub receives tasks, calculates the results and sends them back.
        """
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # needs to store task_id
        self.task_iterator = 0
        self._number_of_workers = 1
        self.__csv_folder = "../worker/scenarios/"

    def connect(self):
        self.logger.info("Using the Stub for the Worker Service Client.")

    def disconnect(self):
        pass

    ####################################################################################################################
    # Supporting methods.
    def _send_task(self, tasks_parameters):
        self.logger.info("Sending task: %s" % tasks_parameters)
        tasks_to_send = []

        for task_parameter in tasks_parameters:
            task_description = dict()
            task_description["task_name"] = self._task_name
            task_description["Scenario"] = self._scenario
            task_description["params"] = {}
            for index, parameter in enumerate(self._task_parameters):
                task_description["params"][parameter] = str(task_parameter[index])
            tasks_to_send.append(task_description)

        for task in tasks_to_send:
            params_to_send = task['params']
            params_to_send['ws_file'] = task['Scenario']['ws_file']

            result = dict()
            if task["task_name"] == "energy_consumption":
                result = self.__energy_consumption(params_to_send)

            elif task["task_name"] == "naiveBayes_mock":
                result = self.__taskNB(params_to_send)

            #  TODO - data is needed
            # elif task["task_name"] is "GA":
            #     result = self._genetic(params_to_send)

            full_result = {
                'worker': 'stub',
                'result': result,
                'task id': self.task_iterator
            }  # for 'energy' must be 'result': {'energy': 23.32}
            # for 'taskNB' must be 'result': {'PREC_AT_99_REC': 0.935}
            self.cur_tasks_ids.append(self.task_iterator)
            self.current_results.append(full_result)
            self.task_iterator += 1

    @staticmethod
    def __str_to_bool(string):
        if string.lower() in ("true"):
            return True
        elif string.lower() in ("false"):
            return False
        else:
            raise ValueError("String \"%s\" is not equal to \"True\" or \"False\"" % string)

    def __energy_consumption(self, param):
        data = []
        path_to_file = self.__csv_folder + "energy_consumption/" + param['ws_file']
        try:
            with open(path_to_file, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if row['FR'] == str(param['frequency']) and row ['TR'] == str(param['threads']):
                        data.append(row)
                    else:
                        continue
        except EnvironmentError:
            self.logger.error("EnvironmentError: file (%s) not found" % path_to_file)

        if data:
            result = choice(data)
            return {
                'energy': float(result["EN"])
            }
        else:
            self.logger.error("Error in Stub (energy_consumption): No data for parameters: %s." % param)

    def __taskNB(self, param):
        data = []
        path_to_file = self.__csv_folder + "rapid_miner/" + param['ws_file']
        try:
            with open(path_to_file, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if self.__str_to_bool(row['laplace_correction']) == self.__str_to_bool(str(param['laplace_correction'])) and \
                            row['estimation_mode'] == str(param['estimation_mode']) and \
                            row['bandwidth_selection'] == str(param['bandwidth_selection']) and \
                            row['bandwidth'] == str(param['bandwidth']) and \
                            row['minimum_bandwidth'] == str(param['minimum_bandwidth']) and \
                            row['number_of_kernels'] == str(param['number_of_kernels']) and \
                            self.__str_to_bool(row['use_application_grid']) == self.__str_to_bool(str(param['use_application_grid'])) and \
                            row['application_grid_size'] == str(param['application_grid_size']):
                        data.append(row)
                    else:
                        continue
        except EnvironmentError:
            self.logger.error("EnvironmentError: file (%s) not found" % path_to_file)

        if data:
            result = choice(data)
            return {
                'PREC_AT_99_REC': float(result["PREC_AT_99_REC"])
            }
        else:
            self.logger.error("Error in Stub (NB): No data for parameters: %s.\n" % param)

    # def _genetic(self, param):
    #     try:
    #         generations = str(param['generations'])
    #         populationSize = str(param['populationSize'])
    #         file_name = "results/scenarios/"+param['ws_file']
    #
    #         import os
    #
    #         command = ("java -jar binary/jastadd-mquat-solver-genetic-1.0.0-SNAPSHOT.jar %s %s %s"
    #                    % (generations, populationSize, param['ws_file']))
    #         os.system(command)
    #
    #         data = Splitter(file_name)
    #         data.searchGA(generations, populationSize, file_name)
    #
    #         result = choice(data.new_data)
    #         return {
    #             'generations': result["generations"],
    #             'populationSize': result["populationSize"],
    #             'Solved': result["Solved"],
    #             'energy': result["Obj"],
    #             'Valid': result["Valid"],
    #             'TimeOut': result["TimeOut"]
    #         }
    #
    #     except Exception as e:
    #         self.logger.error("ERROR IN STUB during performing GA with parameters: %s" % param)


    ####################################################################################################################
    # Outgoing interface for running task(s)
    def work(self, tasks):
        """
        Prepares current tasks, calculates the results, reports all results back.

        :param tasks: list of Configuration instances. The structure of each task's parameters should correspond
                      specified structure in task_configuration["TaskParameters"].
                                         shape - list, e.g. [Configuration1, Configuration2, ...]

        :return: List of dictionaries with result of running all the tasks.
                                         shape - list of dicts, e.g.
                                                 ``[ {
                                                        "worker": "stub",
                                                        "result": {
                                                            "PREC_AT_99_REC": 0.1817
                                                        },
                                                        "taskid": 0
                                                     }
                                                        "worker": "stub",
                                                        "result": {
                                                            "PREC_AT_99_REC": 0.7566
                                                        },
                                                        "taskid": 1
                                                     }
                                                   ]``
                     "worker":           shape - string
                     "result":           shape - dict with keys specified in task_configuration["ResultStructure"]
                     "PREC_AT_99_REC":   shape - specified in task_configuration["ResultDataTypes"]
                     "taskid":           shape - int
        """
        self.cur_tasks_ids = []
        self.current_results = []
        self._send_task(tasks)
        if len(tasks) == len(self.current_results):
            self.logger.info("All tasks (%s) were finished." % len(tasks))
        else:
            self.logger.error("Error: Number of tasks (%s) are not equal to the number of received results (%s)."
                  % (len(tasks), len(self.current_results)))
        self.logger.info("Results: %s" % str(self._report_according_to_required_structure()))
        self._dump_results_to_csv()
        return self.current_results


# A small unit test.
if __name__ == "__main__":
    config = {
        "TaskName"          : "taskNB",
        "Scenario": {
            "ws_file": "taskNB1.csv"
        },
        "TaskParameters"  : ["laplace_correction", "estimation_mode", "bandwidth_selection", "bandwidth", "minimum_bandwidth", "number_of_kernels", "use_application_grid", "application_grid_size"],
        "ResultStructure" : ["PREC_AT_99_REC"],
        "ResultDataTypes" : ["float"],
        "MaxTimeToRunTask": 10
    }
    task_data = [[True, 'full', 'fix', 0.5, 1000, 1000, True, 10000],
                 [True, 'full', 'heuristic', 50, 5, 50, False, 200],
                 [True, 'full', 'fix', 0.5, 5, 100, True, 10000]]
    client = WSClient_Stub(config, 'Stub', 'Stub_WSClient_results.csv')
    results = client.work(task_data)
    logger = logging.getLogger(__name__)
    logger.info(results)
    logger.info("\n end")
