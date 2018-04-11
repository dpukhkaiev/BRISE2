import requests
import json
import time
import csv


class WorkerService(object):

    def __init__(self, experiment_number, host):
        """
        self.State displays state of runner, possible states: Free, TaskSent, ResultsGot
        :param experiment_number: sequence number of experiment to write results
        :param config: dict object {"key": value} - will be sent to slave
        :param host: remote slave address including port "127.0.0.1:8089"
        """
        self.experiment_number = experiment_number
        self.config = None
        self.host = host
        self.path = "http://%s" % self.host
        self.results = None
        self.State = "Free"

    def send_task(self, config):

        if self.State != "Free":
            print("Runner is already busy.")
            return 1
        else:
            self.config = config

        headers = {
            'Type': "AddTask"
        }
        for x in range(10):
            try:
                responce = requests.post(self.path, data=json.dumps(self.config), headers=headers)
                if "OK" not in responce.content:
                    continue
                break
            except requests.RequestException as e:
                print("Failed to send task to %s: %s" %( self.host, e))
        if x == 4: return 1

        self.State = "TaskSent"
        return

    def get_results(self):
        """
        Send one time poll request to get results from the slave
        :return: dict object with results or None in case of faulere
        """
        if self.State != "TaskSent":
            print("Task was not send.")
            return 1

        headers = {
            "Type": "GetResults"
        }
        try:
            responce = requests.get(self.path + "/results", headers=headers)
            try:
                result = responce.content.decode()
                while "\n" in result: result = result.replace("\n", "")
                self.results = json.loads(result)["json"]["Data"]
                self.State = "ResultsGot"
                return self.results
            except Exception as e:
                print("Unable to decode responce: %s\nError: %s" % responce.content, e)
                return None

        except requests.RequestException as e:
            print("Failed to get results from host %s" % self.host)
            return None

    def poll_while_not_get(self, interval = 0.1, timeout = 10):
        """
        Start polling results from host with specified time interval and before timeout elapsed.
        :param interval: interval between each poll request
        :param timeout:  timeout before terminating task
        :return:
        """
        time_start = time.time()
        result = self.get_results()

        while not result:
            result = self.get_results()
            if time.time() - time_start > timeout:
                break
            time.sleep(interval)

        return result

    def write_results_to_csv(self):
        """
        Appends results to "results_ExperimentNumber.csv" file
        :return:
        """
        if self.State != "ResultsGot":
            print("No results to write.")
            return 1

        if not self.results:
            self.get_results()

        # result_fields = ["Threads", "Frequency", "Energy", "Time"]
        # result_fields = ['MinAPIVersion', 'GoVersion', 'Arch', 'ApiVersion', 'Os', 'GitCommit', 'BuildTime', 'Version', 'KernelVersion']
        # if len(self.results) != len(result_fields):
        #     print("ERROR - different number of fields got and needed to be written!")
        #     print("Got:%s\nNeed:%s\n" %(self.results.keys(), result_fields))
        #     return 1
        try:
            with open("results_%s.csv" % self.experiment_number, 'a', newline="") as csvfile:
                writer = csv.DictWriter(csvfile, restval=' ', fieldnames=result_fields)
                writer.writerow(self.results)
                self.State = "Free"
            return 0
        except Exception as e:
            print("Failed to write the results: %s" % e)
            return 1

    def work(self, config):
        self.send_task(config)
        self.poll_while_not_get()
        self.write_results_to_csv()