__doc__ = """
Main module for running benchmark 

Requirements: 
    -   sklearn(with all deps like numpy, scipy : 0.19.1   
    -   sobol_seq
    -   
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from WSClient import WSClient
from regression import Regression, SobolSequence
from repeater import Repeater


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
    from os import path, makedirs
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())

            results_path = config['results_storage']
            if not path.exists(path.dirname(results_path)):
                makedirs(path.dirname(results_path))

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
    # {"task_name": String, "params": Dict, "taskDataPoints": List of points }
    task = load_task()

    # Creating instance of Sobol based on task data for further uniformly distributed data points generation.
    sobol = SobolSequence(dimensionality = len(task["TaskDataPoints"]), data=task["TaskDataPoints"])

    #   Connect to the Worker Service and send task.
    WS = WSClient(task_name=task["task_name"],
                  task_params=task["params"],
                  ws_addr=globalConfig["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (globalConfig['results_storage'], task['params']["FileToRead"]))

    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    runner = Repeater(WS)

    # Need to find default value that we will used in regression to evaluate solution
    print("Getting default best value..")
    default_best_task = task["default_best"]
    default_best_results = runner.measure_task([default_best_task], 'brute_decision')
    default_best_point, default_best_energy = feat_lab_split(default_best_results, task["params"]["ResultFeatLabels"])
    print(default_best_energy)

    # Creating initial set of points for testing and first attempt to create regression model.
    initial_task = sobol.mergeDataWithSobolSeq(numOfPoints=task["params"]["SobolInitLength"])

    # Results will be in a list of points, each point is also a list of values:
    # [[val1, val2,... valN], [val1, val2,... valN]...]
    print("Sending initial task..")
    results = runner.measure_task(initial_task, 'student_deviation', default_point=default_best_results[0])
    print("Results got, splitting to features and labels..")
    features, labels = feat_lab_split(results, task["params"]["ResultFeatLabels"])

    # Generate whole search space for regression.
    search_space = list(itertools.product(*task["TaskDataPoints"]))

    reg_success = False
    while not reg_success:
        # print(features)
        # print(labels)
        reg = Regression(output_filename = "%s%s_regression.txt" % (globalConfig['results_storage'], task['params']["FileToRead"]),
                         test_size = task["params"]["ModelTestSize"],
                         features = features,
                         targets = labels)

        reg_success = reg.regression(param=task["params"],
                                     score_min=0.85,
                                     searchspace=search_space)
        if reg_success:
            print("Model build with accuracy: %s" % reg.accuracy)
            print("Verifying solution that model gave..")
            measured_energy = feat_lab_split(runner.measure_task([reg.solution_features], 'student_deviation'), task["params"]["ResultFeatLabels"])[1][0]

            # If our measured energy higher than default best value - add this point to data set and rebuild model.
            if measured_energy > default_best_energy[0]:
                features += [reg.solution_features]
                labels += [measured_energy]
                print("Predicted energy larger than default.")
                print("Predicted energy: %s. Measured: %s. Best default: %s" %(reg.solution_labels[0], measured_energy[0], default_best_energy[0][0]))
                reg_success = False
                continue

        if not reg_success:
            print("New data point needed to continue building regression. Current number of data points: %s" % str(sobol.numOfGeneratedPoints))
            print('='*100)
            # cur_task = [sobol.getNextPoint()]
            cur_task = [sobol.getNextPoint() for x in range(task['params']['step'])]
            if reg.feature_result:
                cur_task.append(reg.feature_result)
            results = runner.measure_task(cur_task, 'student_deviation', default_point=default_best_results[0])
            new_feature, new_label = feat_lab_split(results, task["params"]["ResultFeatLabels"])
            features += new_feature
            labels += new_label
            if len(features) > len(search_space):
                print("Unable to finish normally, terminating with best results")
                min_en = min(labels)
                min_en_config = features[labels.index(min_en)]
                print("Measured best config: %s, energy: %s" % (str(min_en_config), str(min_en)))
                break

    predicted_energy, predicted_point = reg.solution_labels, reg.solution_features
    print("\n\nPredicted energy: %s, with configuration: %s" % (predicted_energy[0], predicted_point))
    print("Number of measured points: %s" % len(features))
    print("Number of performed measurements: %s" % runner.performed_measurements)
    print("Measured energy is: %s" % str(measured_energy[0]))


if __name__ == "__main__":
    run()
