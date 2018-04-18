import requests
import json
import time
import csv
import os


class WorkerService(object):

    def __init__(self, task_name, features_names, results_structure, experiment_number, host):
        """
        self.State displays state of runner, possible states: Free, TaskSent, ResultsGot
        :param experiment_number: sequence number of experiment to write results
        :param host: remote slave address including port "127.0.0.1:8089"
        """
        self.experiment_number = experiment_number
        self.task_name = task_name
        self.features_names = features_names
        self.config = None
        self.host = host
        self.path = "http://%s" % self.host
        self.State = "Free"
        self.task_body = {}
        self.results = None
        self.results_structure = results_structure
        self.output_filename = ''

    def send_task(self, task):
            """
            :param task: list of points for sending to the WS
            :return: None
            """

            if self.State != "Free":
                print("Runner is already busy.")
                return 1
            else:
                # {
                #     "task_name": "random_1",
                #     "request_type": "send_task",
                #     "params_names": ["param1", "param2", "paramN"],
                #     "param_values": [
                #         [123.0, 123.0, 123.0],
                #         [123.0, 123.0, 123.0]
                #     ],
                #     "worker_config": {
                #         "koko": "2",
                #         "b": "3"
                #     }
                # }
                if len(task) == 0 or len(task[0]) != len(self.features_names):
                    print("%s: Invalid task length in send_task" % self.__module__)
                    return 1

                # self.task_body is a dictionary
                self.task_body["task_name"] = self.task_name
                self.task_body["request_name"] = "send_task"
                self.task_body["params_names"] = self.features_names
                self.task_body["param_values"] = task

            # print("From module %s:\n%s" % (self.__module__, self.task_body))

            headers = {
                'Type': "Send_task"
            }

            try:
                response = requests.post(self.path, data=json.dumps(self.task_body), headers=headers)

                if response.status_code != 200:
                    print("Incorrect response code from server: %s\nBody:%s" % (response.status_code, response.content))
                    return 1

                response = response.content.decode()
                response = response.replace("\n", "")

                response = json.loads(response.content)
                # In responce Worker Service will send IDs for each task.
                # Response body will be like:
                # {
                #         "task_name": "random_1",
                #         "response_type": "send_task",
                #         "ID": [123123123, 1231231234, 1231231235]
                # }
                # Saving IDs for further polling results and etc.

                self.task_body["ID"] = response["ID"]

            except requests.RequestException or json.JSONDecodeError as e:
                print("Failed to send task to %s: %s" % (self.host, e))
                return 1
            except json.JSONDecodeError as e:
                print("Failed to decode response for send task request:" % e)
                return 1
            self.State = "TaskSent"
            # return self.task_body

    def get_results(self):
        """
        Send one time poll request to get results from the slave
        :return: list of data points with requested structure
        """
        if self.State != "TaskSent":
            print("Task was not send.")
            return 1

        headers = {
            "Type": "GetResults"
        }
        # Results polling will be in view of:
        # {
        #     "task_name": "random_1",
        #     "request_type": "get_results",
        #     "response_struct": ["param1", "param2", "paramN"],
        #     "ID": [123123123, 123123124, 123123125]
        # }
        data = {
            "task_name": self.task_body["task_name"],
            "request_type": "get_results",
            "response_struct": self.results_structure,
            "ID": self.task_body["ID"]
        }

        try:
            response = requests.post(self.path, data=data, headers=headers)
            if response.status_code != 200:
                print("Incorrect response code from server: %s\nBody:%s" % (response.status_code, response.content))
                return 1
            try:
                response = response.content.decode()
                response = response.replace("\n", "")
                # Response will be in structure:
                #   {
                #       "task_name": "random_1",
                #       "request_type": "get_results",
                #       "params_names": ["param1", "param2", "paramN"],
                #       "param_values": [
                #           [123, "value_for_param_2", 123.1],
                #           [112313253, "value2_for_param_2", 123123.1],
                #           [123, None, None]
                #       ]
                #   }

                results = json.loads(response)

                self.results = results["param_values"]

                if "progress" not in response:
                    self.State = "ResultsGot"

                return self.results

            except Exception as e:
                print("Unable to decode responce: %s\nError: %s" % response.content, e)
                return None

        except requests.RequestException as e:
            print("Failed to get results from WS %s, error: %s" % (self.host, e))
            return None

    def poll_while_not_get(self, interval=0.5, timeout=30):
        """
        Start polling results from host with specified time interval and before timeout elapsed.
        :param interval: interval between each poll request
        :param timeout:  timeout before terminating task
        :return: list of data points with requested structure
        """
        if self.State != "TaskSent":
            print("Task was not send.")
            return 1

        time_start = time.time()
        self.results = self.get_results()

        while self.State != "ResultsGot":
            self.get_results()
            if time.time() - time_start > timeout:
                break
            time.sleep(interval)

        return self.results

    def write_results_to_csv(self):
        """
        Appends results to CSV file. Filename based on task config - Task name and experiment number.
        In case if file exists - data will be appended, if not - file will be created.
        Structure based on self.results_structure
        :return:
        """
        if self.State != "ResultsGot":
            print("Results are not ready to be written.")
            return 1

        # Formulating output_filename
        self.output_filename = "{task_name}_{ExNum}_results.csv".format(task_name=self.config["task_name"],
                                                            ExNum=self.experiment_number)

        # Creating file if not exists
        file_exists = os.path.isfile(self.output_filename)
        if not file_exists:
            with open(self.output_filename, 'w') as f:
                legend = ''
                for column_type in self.results_structure:
                    for column_name in self.results_structure[column_type]:
                        legend += column_type + "_" + column_name + ", "
                f.write(legend[:legend.rfind(', ')] + '\n')

        # Writing the results
        try:
            with open(self.output_filename, 'a', newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for result in self.results:
                    writer.writerow(result)
                self.State = "Free"
            return 0
        except Exception as e:
            print("Failed to write the results: %s" % e)
            return 1

    def ping(self):
        """
        Method checks availability of Worker Service.
        :return: True if service available, False if not or error occurred (IP does not available or etc).
        """
        try:
            resp = requests.get(self.host + "/ping")
            if "pong" not in resp.content:
                print("Ping does not have OK response.")
                return False
            else:
                return True
        except Exception as e:
            print("Error in ping method: %s" % e)
            return False

    def work(self, task):
        self.send_task(task)
        self.poll_while_not_get()
        self.write_results_to_csv()
        return self.results
