import csv
import logging
import uuid
from random import choice

from WorkerServiceClient.WSClient_events import WSClient


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

    ####################################################################################################################
    # Supporting methods.

    def is_all_tasks_finish(self, id_measurement):
        """
        Checking are all tasks for specific configuration finish or not
        :param id_measurement: id specific measurement
        :return: True or False
        """
        if len(self.measurement[id_measurement]['task_results']) == len(self.measurement[id_measurement]['tasks_to_send']):
            return True
        else:
            return False

    def is_measurement_finish(self, id_measurement):
        """
        Checking is specific measurement finish or not
        :param id_measurement: id specific measurement
        :return: True or False
        """
        for configuration in self.measurement[id_measurement].keys():
            if self.measurement[id_measurement][configuration]['status'] != "Finished":
                return False
        return True

    def _send_measurement(self, id_measurement, measurement):

        self.logger.info("Sending measurement: %s" % id_measurement)

        tasks_to_send = []
        self.measurement[id_measurement]['tasks_results'] = []
        number_ready_task = len(measurement['tasks_results'])
        for i, task_parameter in enumerate(measurement['tasks_to_send']):
            if i >= number_ready_task:
                self.logger.info("Sending task: %s" % task_parameter)
                task_description = dict()
                task_description["id_measurement"] = id_measurement
                task_description["task_name"] = self._task_name
                task_description["time_for_run"] = self._time_for_one_task_running
                task_description["scenario"] = self._scenario
                task_description["params"] = {}
                for index, parameter in enumerate(self._task_parameters):
                    task_description["params"][self._task_parameters[index]] = str(task_parameter[index])

                tasks_to_send.append(task_description)

        for task in tasks_to_send:
            params_to_send = task['params']
            params_to_send['ws_file'] = task['scenario']['ws_file']

            result = dict()
            if task["task_name"] == "energy_consumption":
                result = self.__energy_consumption(params_to_send)

            elif task["task_name"] == "naiveBayes_mock":
                result = self.__taskNB(params_to_send)

            #  TODO - data is needed
            # elif task["task_name"] is "GA":
            #     result = self._genetic(params_to_send)

            task['result'] = result
            # for 'energy' must be 'result': {'energy': 23.32}
            # for 'taskNB' must be 'result': {'PREC_AT_99_REC': 0.935}

            task['task id'] = str(uuid.uuid4())
            task['worker'] = 'stub'
            self.measurement[task['id_measurement']]['tasks_results'].append(task)

            if self.is_all_tasks_finish(task['id_measurement']):
                self.measurement[task['id_measurement']][task['configuration']]['status'] = "Finished"
                if self.is_measurement_finish(task['id_measurement']):
                    return 0
        return -1


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
    def work(self, j_conf, tasks):
        measurement_id = str(uuid.uuid4())
        self.measurement[measurement_id] = {}
        self.measurement[measurement_id]["tasks_to_send"] = tasks
        self.measurement[measurement_id]["tasks_results"] = []
        self.measurement[measurement_id]["configuration"] = j_conf
        try:
           result_code = self._send_measurement(measurement_id, self.measurement[measurement_id])
           if result_code != 0:
               self.logger.error("Error: Not all tasks were finished")
        except Exception as er:
            self.logger.error("Error: {er}".format(er=er))
        self.dump_results_to_csv()
        return self.measurement


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
    configurations = [[True, 'full', 'fix', 0.5, 1000, 1000, True, 10000],
                 [True, 'full', 'heuristic', 50, 5, 50, False, 200],
                 [True, 'full', 'fix', 0.5, 5, 100, True, 10000]]
    measurement = {}
    is_measurement_need_to_send = True
    # Creating holders for current measurements
    for configuration in configurations:
        # Evaluating each Configuration in configurations list
        needed_tasks_count = 1
        measurement[str(configuration)] = {'parameters': configuration,
                                                            'needed_tasks_count': needed_tasks_count,
                                                            'tasks_to_send': [], 'task_results': [], 'task_ids': [],
                                                            'task_workers': [], 'type': type,
                                                            'status': "InProgress"}
    for point in measurement.keys():
        for i in range(measurement[point]['needed_tasks_count']):
            measurement[point]['tasks_to_send'].append(measurement[point]['parameters'])

    client = WSClient_Stub(config, 'event_service', 49153, 'Stub_WSClient_results.csv')
    results = client.work(measurement)
    logger = logging.getLogger(__name__)
    logger.info(results)
    logger.info("\n end")
