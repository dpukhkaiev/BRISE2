import requests
import json
import time
import csv
import os


class WorkerService(object):

    def __init__(self, task_name, features_names, results_structure, experiment_number, WSFile, host):
        """
        self.State displays state of runner, possible states: Free, TaskSent, ResultsGot
        :param experiment_number: sequence number of experiment to write results
        :param host: remote slave address including port "127.0.0.1:8089"
        """
        self.host = host
        self.path = "http://%s" % self.host
        while not self.ping():
            print("WS does not available, retrying after 5 seconds..")
            time.sleep(5)

        self.experiment_number = experiment_number
        self.WSFile = WSFile
        self.task_name = task_name
        self.features_names = features_names
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
                #         "ws_file": "name of file that will be read"
                #         "b": "3"
                #     }
                # }
                if len(task) == 0 or len(task[0]) != len(self.features_names):
                    print("%s: Invalid task length in send_task" % self.__module__)
                    return 1

                # self.task_body is a dictionary
                self.task_body["task_name"] = self.task_name
                self.task_body["request_type"] = "send_task"
                self.task_body["params_names"] = self.features_names
                self.task_body["param_values"] = task
                self.task_body["worker_config"] =  {
                    "ws_file": self.WSFile
                }

            # print("From module %s:\n%s" % (self.__module__, self.task_body))

            headers = {
                'Type': "Send_task",
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(self.path + "/task/add", data=json.dumps(self.task_body), headers=headers)

                if response.status_code != 201:
                    print("Incorrect response code from server: %s\nBody:%s" % (response.status_code, response.content))
                    exit()

                response = response.content.decode()
                response = response.replace("\n", "")
                response = json.loads(response)
                # In responce Worker Service will send IDs for each task.
                # Response body will be like:
                # {
                #         "task_name": "random_1",
                #         "response_type": "send_task",
                #         "id": [123123123, 1231231234, 1231231235]
                # }
                # Saving IDs for further polling results and etc.
                self.task_body['id'] = response['id']

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
            'Content-Type': 'application/json'
        }
        # Results polling will be in view of:
        # {
        #     "task_name": "random_1",
        #     "request_type": "get_results",
        #     "response_struct": ["param1", "param2", "paramN"],
        #     "id": [123123123, 123123124, 123123125]
        # }
        data = {
            "task_name": self.task_body["task_name"],
            "request_type": "get_results",
            "response_struct": self.results_structure,
            "id": self.task_body["id"]
        }

        try:
            # print(json.dumps(data))
            response = requests.put(self.path + '/result/format', data=json.dumps(data), headers=headers)
            if response.status_code != 200:
                print("Incorrect response code from server on getting results: %s\nBody:%s" % (response.status_code, response.content))
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
                if "in progress" not in results["statuses"]:
                    self.State = "ResultsGot"
                    # need to cast string values to float values

                    for index, point in enumerate(self.results):
                        try:
                            self.results[index] = [float(x) for x in point]
                        except:
                            self.results[index] = point

                return self.results

            except Exception as e:
                print("Unable to decode responce: %s\nError: %s" % (response, e))
                return None

        except requests.RequestException as e:
            print("Failed to get results from WS %s, error: %s" % (self.host, e))
            return None

    def poll_while_not_get(self, interval=3, timeout=90, terminate=False):
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
                if terminate:
                    response = requests.delete(self.path + '/terminate/'+'id' headers=headers)
                else: break
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
        self.output_filename = "{task_name}_{ExNum}_results.csv".format(task_name=self.task_name, ExNum=self.experiment_number)

        # Creating file if not exists
        file_exists = os.path.isfile(self.output_filename)
        if not file_exists:
            with open(self.output_filename, 'w') as f:
                legend = ''
                for column_name in self.results_structure:
                    legend += column_name + ", "
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
            resp = requests.get(self.path + "/ping")
            if "pong" not in resp.content.decode():
                print("Ping does not have OK response.")
                return False
            else:
                return True
        except Exception as e:
            print("Error in ping method: %s" % e)
            return False

    def work(self, task):
        print("sending task")
        self.send_task(task)
        print("polling results..")
        time.sleep(2)   # TODO: need to fix this issue from the WS site - it could happen that generated IDs not in stack yet.
        self.poll_while_not_get()
        self.write_results_to_csv()
        return self.results
