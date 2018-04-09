import docker

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import threading
import json
import time
import os
import fnmatch
import csv
import requests
import sobol_seq
import numpy

def runRemoteContainer(host, image):

    # Creating client object that reflects connection to remote docker daemon
    # Verifying that connection is established
    try:
        client = docker.DockerClient(
            base_url='tcp://' + host['ip'] + ':' + str(host['port']))
        pingIsOk = client.ping()
        
        if pingIsOk: print("Ping is OK, remote daemon %s is available!" % host['ip'])
        else:
            print("Unable to recieve proper ping responce from %s, check script/docker configuration." % host['ip'])
            return 3
    except docker.errors.APIError as e:
        print(e)
        return 3

    #   Listing images in remote machine and downloading image from Docker hub if needed
    client_images = []
    for img in client.images.list():
        client_images += img.tags

    if str(image["name"] + image["tag"]) not in client_images:
        try:
            client.images.pull(image["name"], image["tag"])

        except docker.errors.APIError as e:
            print("Unable to load docker image from Docker hub: %s" % e)
            return 3

    else:
        print("Needed image already exists in %s" % host['ip'])

    # Running docker container on remote host.
    # TODO - change it to building normal container from normal dockerfile that will copy all needed files to remote host and rung entry point (Python script)
    container = client.containers.run(image=image["name"] + image["tag"], detach=True)
    # print "Container logs:"
    # print container.logs()
    return 0


def startServer(port=8089):

    class S(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_GET(self):
            self._set_headers()
            parsed_path = urllib.parse.urlparse(self.path)
            request_id = parsed_path.path
            
            self.wfile.write("Hello\nRequest ID:%s\npath:%s" % (request_id, parsed_path))

        def do_POST(self):
            self._set_headers()
            parsed_path = urllib.parse.urlparse(self.path)
            request_id = parsed_path.path

            # TODO - write parcer for JSON responce from clients
            with open("client_responces.log", 'a') as logfile:
                try:
                    
                    request = self.request
                except: pass


            with open('WebServ.log', 'a') as logfile:
                logfile.write('%s - - [%s] %s\n'%
                                (self.client_address[0],
                                self.log_date_time_string(),
                                self.request))
            
            self.wfile.write("Hello\nRequest ID:%s\npath:%s" % (request_id, parsed_path))

        def do_HEAD(self):
            self._set_headers()
        


    def run(server_class=HTTPServer, handler_class=S, port=port):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print('Starting httpd...')
        httpd.serve_forever()
    
    run()


def readConfig(fileName='config.json'):
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())
            return config

    except IOError as e:
        print('No config file found!')
        print(e)
        # return {}
        exit(3)
    except ValueError as e:
        print('Invalid config file!')
        print(e)
        # return {}
        exit(3)


def run_sobol(path_to_sobol_file="/home/sem/TMP/BRISE/"):
    # This method runs local sobol.R script for getting "pseudorandom" starting configuration

    # Prepare experiment number, will be used in following methods.
    experiment_number = 0
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, "sobol_output_*.csv"):
            tmp_experiment_number = int(file.replace("sobol_output_", "").replace(".csv", ""))
            if experiment_number <= tmp_experiment_number:
                experiment_number = tmp_experiment_number + 1

    #   sobol.R run to generate config file
    sobolFile = "sobol_output_" + str(experiment_number) + ".csv"

    execution_result = os.system("Rscript %ssobol.R 96 %s" % (path_to_sobol_file, sobolFile))

    #   If running sobol.R script failed - read the last one
    if execution_result != 0:
        # Finding the "freshest" "sobolFile..."
        sobolFile = ['sobol_output_.txt', 0] # [name, last modification time]
        for file in os.listdir('.'):
            if fnmatch.fnmatch(file, 'sobol_output_*.csv'):
                if os.stat(file).st_mtime > sobolFile[1]:
                    sobolFile[0] = file
                    sobolFile[1] = os.stat(file).st_mtime

    # Reading sobol script output to list [(#ofThreads, frequency)]
    with open(sobolFile, 'r') as f:
        sobol_output = []
        reader = csv.DictReader(f)
        for line in reader:
            sobol_output.append((float(line["TR"]), float(line["FR"])))

    # Mapping sobol.R output to real configuration
    # looks like something weird

    freqs = [1200., 1300., 1400., 1600., 1700., 1800., 1900., 2000., 2200., 2300., 2400., 2500., 2700., 2800.,
             2900., 2901.]
    threads = [1, 2, 4, 8, 16, 32]
    config = []
    for point in sobol_output:
        config.append([threads[int(point[0])-1], freqs[int(point[1]) - 1]])

    return [experiment_number, config]


def generate_sobol_seq(dimensionality=2, sizes=(6, 16), number_of_data_points='all'):
    """
        Generates sobol sequence of uniformly distributed data points in N dimensional space.
        :param dimensionality: - number of different parameters in greed.
        :param sizes: - number of different allowed values in each parameter, for Energy consumption parameters greed we have 6 threads and 16 frequencies.
        :param number_of_data_points: int or str "all"
        :return: sobol sequence as numpy array.
    """
    if len(sizes) != dimensionality:
        print("Error in Sobol sequence generator: different number of dimensions and given sizes of dimensions.")
        return

    else:
        if number_of_data_points == "all":
            number_of_data_points = 1
            for x in sizes:
                number_of_data_points *= int(x)
        else:
            pass

        return sobol_seq.i4_sobol_generate(dimensionality, number_of_data_points)


def merge_params_with_sobol_seq(params, sobol_seq=None):
    """
    Method maps input parameter points to uniformly generated sobol sequence and returns data points.
    Number of parameters should be the same as depth of each point in Sobol sequence.
    It is possible to call method without providing Sobol sequence - it will be generated in runtime.
    :param params: list of iterable parameter values
    :param sobol_seq: data points
    :return: List with uniformly distributed parameters across parameter space.
    """

    if type(sobol_seq) is numpy.ndarray:
        if len(params) != len(sobol_seq[0]):
            print("Warning! Number of provided parameters does not match with size of Sobol sequence. Generating own Sobol sequence based on provided parameters.")
            sobol_seq = None

    if not sobol_seq or type(sobol_seq) is not numpy.ndarray:
        sizes = []
        for parameter in params:
            sizes.append(len(parameter))
        sobol_seq = generate_sobol_seq(len(params), sizes, "all")

    # Following loop apply Sobol grid to given parameter grid, e.g.:
    # for Sobol array(
    #  [[ 0.5  ,  0.5  ],
    #   [ 0.75 ,  0.25 ],
    #   [ 0.25 ,  0.75 ],
    #   [ 0.375,  0.375],
    #   [ 0.875,  0.875]])
    #
    # And params = [
    # [1, 2, 4, 8, 16, 32],
    # [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
    #   2900.0, 2901.0]
    #               ]
    # We will have output like:
    # [[3.0, 8.0],
    #  [4.5, 4.0],
    #  [1.5, 12.0],
    #  [2.25, 6.0],
    #  [5.25, 14.0]]
    result = []
    for point in sobol_seq:
        result.append([parameter_value * len(params[parameter_index]) for parameter_index, parameter_value in enumerate(point)])

    return result


class TaskRunner(object):

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

    def write_results(self):
        """
        Appends results to "results_ExperimentNumber.csv" file
        :return:
        """
        if self.State != "ResultsGot":
            print("No results to write.")
            return 1

        if not self.results:
            self.get_results()

        result_fields = ["Threads", "Frequency", "Energy", "Time"]
        # result_fields = ['MinAPIVersion', 'GoVersion', 'Arch', 'ApiVersion', 'Os', 'GitCommit', 'BuildTime', 'Version', 'KernelVersion']
        if len(self.results) != len(result_fields):
            print("ERROR - different number of fields got and needed to be written!")
            print("Got:%s\nNeed:%s\n" %(self.results.keys(), result_fields))
            return 1
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
        self.write_results()


def run():

    #   Reading config file 
    worker_set = readConfig()
    if not worker_set:
        print('Unable to start script, no configuration!')
        return

    #   Starting http server to recieve responce from containers at background
    # server_thread = threading.Thread(target=startServer)
    # server_thread.start()
    # time.sleep(2) # to start a httpd

    #   Start runnig containters on remote daemons
    for worker in list(worker_set.keys()):
        runRemoteContainer(worker_set[worker], worker_set[worker]["image"])
    #   After finishing running containers - join server thread to main thread
    # server_thread.join()

    #   Running sobol R script for generation of tasks
    exp_number, tasks_list = run_sobol()

    # Function that runs one worker
    def map_task(worker):
        global tasks_list
        while tasks_list:
            try:
                task = tasks_list.pop()
                task = {"TR": task[0], "FR": task[1]}
                worker.work(task)
            except IndexError:
                return

    # Create worker instances
    for worker in worker_set:
        worker_WS_addr = "http://%s:8080" % worker['ip']
        worker_set[worker]["instance"] = TaskRunner(exp_number, worker_WS_addr)

    # Start swarming :)
    for worker in worker_set:
        threading.Thread(target=map_task, args=worker["instance"]).start()

    while threading.active_count() > 0:
        time.sleep(0.5)

if __name__ == "__main__":
    run()
