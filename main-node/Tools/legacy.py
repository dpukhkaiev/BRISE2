import docker
import os
import fnmatch
import csv
import numpy
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer


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

def cartesian_product(*arrays):
    la = len(arrays[0])
    dtype = numpy.result_type(*arrays[0])
    arr = numpy.empty([len(a) for a in arrays[0]] + [la], dtype=dtype)
    for i, a in enumerate(numpy.ix_(*arrays[0])):
        arr[...,i] = a
    return arr.reshape(-1, la)

def readGlobalConfig1(fileName='./GlobalConfig.json'):
    from os import path, makedirs
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())

            results_path = config['results_storage']
            if not path.exists(path.dirname(config['results_storage'])):
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
