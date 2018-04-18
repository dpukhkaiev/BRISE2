__doc__ = """
Main module for running benchmark 

Requirements: 
    -   sklearn(with all deps like numpy, scipy : 0.19.1   
    -   sobol_seq
    -   
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from WorkerService import WorkerService
from regression import Regression


import urllib.parse
import json
import sobol_seq
import numpy

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
        dimmensions = task["params"]["DimensionNames"]
        with open(dataFile) as f:
            data = json.loads(f.read())[task["task_name"]]
            taskDataPoints = []
            for dimension in dimmensions:
                taskDataPoints.append(numpy.array(data[dimension]))
    except IOError as e:
        print("Error with reading task.json file: %s" % e)
        exit(1)
    except json.JSONDecodeError as e:
        print("Error with decoding task: %s" % e)
        exit(1)
    return {"task_name"          : task["task_name"],
            "params"        : task["params"],
            "TaskDataPoints"    : taskDataPoints}

def cartesian_product(*arrays):
    la = len(arrays[0])
    dtype = numpy.result_type(*arrays[0])
    arr = numpy.empty([len(a) for a in arrays[0]] + [la], dtype=dtype)
    for i, a in enumerate(numpy.ix_(*arrays[0])):
        arr[...,i] = a
    return arr.reshape(-1, la)

class SobolSequence():

    def __init__(self, dimensionality, data):
        """
        Creates SobolSequence instance that stores information about number of generated poitns
        :param dimensionality: - number of different parameters in greed.

        """
        self.dimensionality = dimensionality
        self.data = data
        self.numOfGeneratedPoints = 0

    def __generate_sobol_seq(self, number_of_data_points=1, skip = 0):
        """
            Generates sobol sequence of uniformly distributed data points in N dimensional space.
            :param number_of_data_points: int - number of points that needed to be generated in this iteration
            :return: sobol sequence as numpy array.
        """

        sequence = sobol_seq.i4_sobol_generate(self.dimensionality, skip + number_of_data_points)[skip:]
        self.numOfGeneratedPoints += number_of_data_points

        return sequence

    def getNextPoint(self):
        """
        Will return next data point from initiated Sobol sequence.
        :return:
        """
        # Cut out previously generated points.
        skip = self.numOfGeneratedPoints

        # Point is a list with floats uniformly distributed between 0 and 1 for all parameters [paramA, paramB..]
        point = self.__generate_sobol_seq(skip=skip)[0]

        result = []
        # In loop below this distribution imposed to real parameter values list.
        for parameter_index, parameterValue in enumerate(point):
            result.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])

        return result

    def mergeDataWithSobolSeq(self, sobol_seq=None, numOfPoints = 'all'):
        """
        Method maps input parameter points to uniformly generated sobol sequence and returns data points.
        Number of parameters should be the same as depth of each point in Sobol sequence.
        It is possible to call method without providing Sobol sequence - it will be generated in runtime.
        :param sobol_seq: data points
        :param numOfPoints: 'all' - all parameters will be mapped to sobol distribution function, or int
        :return: List with uniformly distributed parameters across parameter space.
        """

        if type(sobol_seq) is numpy.ndarray:
            if len(self.data) != len(sobol_seq[0]):
                print("Warning! Number of provided parameters does not match with size of Sobol sequence. Generating own Sobol sequence based on provided parameters.")
                sobol_seq = None

        # The below 'if' case generates sobol sequence
        if not sobol_seq or type(sobol_seq) is not numpy.ndarray:

            if numOfPoints == 'all':
                numOfPoints = 1
                for parameter in self.data:
                    numOfPoints *= len(parameter)

            sobol_seq = self.__generate_sobol_seq(numOfPoints)

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
            tmp_res = []
            for parameter_index, parameterValue in enumerate(point):
                tmp_res.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])
            result.append(tmp_res)
        return result


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
        results['lamels'].append(to_labels)
    return results['features'], results['labels']

def run():

    #   Reading config file 
    globalConfig = readGlobalConfig()

    #   Loading task config and creating config points distribution according to Sobol.
    # {"task_name": String, "params": Dict, "taskDataPoints": List of ndarrays }
    task = load_task()

    # Creating instance of Sobol based on task data for further uniformly distributed data points generation.
    sobol = SobolSequence(dimensionality = len(task["TaskDataPoints"]), data=task["TaskDataPoints"])

    # Creating initial set of points for testing and first attempt to create regression model.
    initial_task = sobol.mergeDataWithSobolSeq(numOfPoints=task["params"]["SobolInitLength"])

    # Preparing task request for sending it to the WS.

    #   Connect to the Worker Service and send task.
    results_structure = ["frequency", "threads", "energy", "exe_time", "state_time"]
    feat_and_labels_structure = ['feature', 'feature', 'label']

    WS = WorkerService(task_name=task["task_name"],
                       features_names=task["params"]["DimensionNames"],
                       results_structure=results_structure,
                       experiment_number=task["params"]["ExperimentNumber"],
                       host=globalConfig["WorkerService"]["Address"])
    # Check availability of WS
    # if not WS.ping():
    #     print("WS does not available, shutting down.")
    #     return 1
    # else:

    # Results will be in a list of points, each point is also a list of values:
    # [[val1, val2,... valN], [val1, val2,... valN]...]
    results = WS.work(initial_task)

    features, labels = feat_lab_split(results, feat_and_labels_structure)

    reg_model = Regression("",
                           task["params"]["InitTrain_size"],
                           features,
                           labels)

    model_is_accurate = reg_model.regression(filename=WS.output_filename,
                                          param='noParam',
                                          degree=6,  # found in start.py of BRISE
                                          r2_min=0.8)
    search_space = cartesian_product(task["TaskDataPoints"])

    energy = -1
    features = []

    while not model_is_accurate or energy < 0:
        print("Model is not valid, running new task. Checked points by Sobol: %s" % sobol.numOfGeneratedPoints)
        cur_task = sobol.getNextPoint()
        results = WS.work(cur_task)
        new_feature, new_label = feat_lab_split(results, feat_and_labels_structure)
        features += new_feature
        labels += new_label

        reg_model = Regression("",
                               task["params"]["InitTrain_size"],
                               features,
                               labels)

        model_is_accurate = reg_model.regression(filename=WS.output_filename,
                                   param='noParam',
                                   degree=6,  # found in start.py of BRISE
                                   r2_min=0.99)
        if model_is_accurate:
            energy, features = reg_model.find_optimal(search_space)




if __name__ == "__main__":
    run()
