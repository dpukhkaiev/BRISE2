__doc__ = """
Main module for running benchmark 

Requirements: 
    -   sklearn(with all deps like numpy, scipy : 0.19.1   
    -   sobol_seq
    -   
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from WorkerService import WorkerService
from regression import Regression, SobolSequence


import urllib.parse
import json
import numpy
import itertools

# disable warnings for demonstration.
from warnings import filterwarnings
filterwarnings("ignore")

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


def readGlobalConfig(fileName='./GlobalConfig.json'):
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


def load_task(path_to_file="./task.json"):
    """
    Method reads task.json file where task name and task parameters, that are needed to be sent to the workers specified.
    :param path_to_file: sting path to task file.
    :return: dict with task name, task parameters and task data in ndarray
    """
    try:
        with open(path_to_file, 'r') as taskFile:
            task = json.loads(taskFile.read())
            # return task
        dataFile = task["params"]["DataFile"]
        dimmensions = task["params"]["FeatureNames"]
        with open(dataFile) as f:
            data = json.loads(f.read())[task["task_name"]]
            taskDataPoints = []
            for dimension in dimmensions:
                taskDataPoints.append(data["all_data"][dimension])
    except IOError as e:
        print("Error with reading task.json file: %s" % e)
        exit(1)
    except json.JSONDecodeError as e:
        print("Error with decoding task: %s" % e)
        exit(1)
    return {"task_name"         : task["task_name"],
            "params"            : task["params"],
            "TaskDataPoints"    : taskDataPoints,
            "default_best"      : data["default_best"]}


def cartesian_product(*arrays):
    la = len(arrays[0])
    dtype = numpy.result_type(*arrays[0])
    arr = numpy.empty([len(a) for a in arrays[0]] + [la], dtype=dtype)
    for i, a in enumerate(numpy.ix_(*arrays[0])):
        arr[...,i] = a
    return arr.reshape(-1, la)


def feat_lab_split(data, structure):

    # need to rewrite it in normal way..

    results = {"features": [],
               "labels": []
               }

    for point in data:
        to_features = []
        to_labels = []
        for index, type in enumerate(structure):
            if type == '1' or type == 'feature':
                to_features.append(point[index])
            else:
                to_labels.append(point[index])
        results['features'].append(to_features)
        results['labels'].append(to_labels)
    return results['features'], results['labels']

def run():

    #   Reading config file 
    globalConfig = readGlobalConfig()

    #   Loading task config and creating config points distribution according to Sobol.
    # {"task_name": String, "params": Dict, "taskDataPoints": List of ndarrays }
    task = load_task()

    # Creating instance of Sobol based on task data for further uniformly distributed data points generation.
    sobol = SobolSequence(dimensionality = len(task["TaskDataPoints"]), data=task["TaskDataPoints"])

    #   Connect to the Worker Service and send task.
    WS = WorkerService(task_name=task["task_name"],
                       features_names=task["params"]["FeatureNames"],
                       results_structure=task["params"]["ResultStructure"],
                       experiment_number=task["params"]["ExperimentNumber"],
                       host=globalConfig["WorkerService"]["Address"])

    # Need to find default value that we will used in regression to evaluate solution
    print("Getting default best value..")
    default_best_task = task["default_best"]
    default_best_results = WS.work([default_best_task])
    default_best_point, default_best_energy = feat_lab_split(default_best_results, task["params"]["ResultFeatLabels"])
    print(default_best_energy)

    # Creating initial set of points for testing and first attempt to create regression model.
    initial_task = sobol.mergeDataWithSobolSeq(numOfPoints=task["params"]["SobolInitLength"])

    # Results will be in a list of points, each point is also a list of values:
    # [[val1, val2,... valN], [val1, val2,... valN]...]
    print("Sending initial task..")
    results = WS.work(initial_task)
    print("Results got, splitting to features and labels..")
    features, labels = feat_lab_split(results, task["params"]["ResultFeatLabels"])

    # Generate whole search space for regression.
    search_space = list(itertools.product(*task["TaskDataPoints"]))

    reg_success = False
    while not reg_success:
        reg = Regression(output_filename = "%s_regression.txt" % task["task_name"],
                         test_size = task["params"]["ModelTestSize"],
                         features = features,
                         targets = labels)

        reg_success = reg.regression(param=task["params"],
                                        score_min=0.5,
                                        searchspace=search_space)
        if reg_success:
            print("Model build with accuracy: %s" % reg.accuracy)
            print("Verifying solution that model gave..")
            measured_energy = feat_lab_split(WS.work([reg.solution_features]), task["params"]["ResultFeatLabels"])[1][0]

            # If our measured energy higher than default best value OR
            # Our predicted energy deviates for more than 10% from measured - take new point.
            if measured_energy > default_best_energy[0] or \
                    abs(measured_energy[0] - reg.solution_labels[0]) > measured_energy[0] * 0.1:

                print("Predicted energy larger than default, or deviation too big.")
                print("Predicted energy: %s. Measured: %s. Best default: %s" %(reg.solution_labels[0], measured_energy[0], default_best_energy[0][0]))
                reg_success = False

        if not reg_success:
            print("New data point needed to continue building regression. Current number of data points: %s" % str(sobol.numOfGeneratedPoints))
            cur_task = [sobol.getNextPoint()]
            results = WS.work(cur_task)
            new_feature, new_label = feat_lab_split(results, task["params"]["ResultFeatLabels"])
            features += new_feature
            labels += new_label

    predicted_energy, predicted_point = reg.solution_labels, reg.solution_features
    print("\n\nPredicted energy: %s, with configuration: %s" % (predicted_energy[0], predicted_point))
    print("Measured energy is: %s" % str(measured_energy[0]))


if __name__ == "__main__":
    run()
