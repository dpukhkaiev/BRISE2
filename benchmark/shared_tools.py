import sys
import pickle
import random
import requests
import datetime
import socketio  # high-level transport protocol
import logging
import socket # low-level (3-4th levels of OSI model), binding IP and port
import json
import time
import re
import os
from typing import Union
from string import ascii_lowercase

import plotly.io as pio

sys.path.append('/app')
from core_entities import configuration, experiment

# COLORS = [
    # '#1f77b4',  # muted blue
    # '#ff7f0e',  # safety orange
    # '#2ca02c',  # cooked asparagus green
    # '#d62728',  # brick red
    # '#9467bd',  # muted purple
    # '#8c564b',  # chestnut brown
    # '#e377c2',  # raspberry yogurt pink
    # '#7f7f7f',  # middle gray
    # '#bcbd22',  # curry yellow-green
    # '#17becf'   # blue-teal
# ]
COLORS = [
    '#ff8b6a',
    '#00d1cd',
    '#eac100',
    '#1f77b4',
    '#8c564b',
    '#621295',
    '#acdeaa',
    '#bcbd22',
    '#00fa9a',
    '#ff7f0e',
    '#f2c0ff',
    '#616f39',
    '#f17e7e'
]


def restore(*args, workdir="./results/serialized/", **kwargs):
    """ De-serializing a Python object structure from binary files.

    Args:
        workdir (str, optional): Path to Experiment instances. Defaults to "./results/serialized/".

    Returns:
        List: The list of Experiment instances.
    """

    exp = []
    for index, file_name in enumerate(args):
        with open(workdir + file_name, 'rb') as input:
            instance = pickle.load(input)
            instance.color = COLORS[index % len(COLORS)]
            exp.append(instance)
    return exp


def export_plot(plot, wight=600, height=400, path='./results/reports/', file_format='.svg'):
    """ Export plot in another format. Support vector and raster - svg, pdf, png, jpg, webp.

    Args:
        plot (Plotly dictionary): Layout of plot with data
        wight (int, optional): Wight of output image. Defaults to 600.
        height (int, optional): Height of output image. Defaults to 400.
        path (str, optional): Path to export the file. Defaults to './results/reports/'.
        file_format (str, optional): Export file format. Defaults to '.svg'.
    """
    name = ''.join(random.choice(ascii_lowercase) for _ in range(10)) + file_format
    pio.write_image(plot, path+name, width=wight, height=height)


def get_resource_as_string(name, charset='utf-8'):
    with open(name, "r", encoding=charset) as f:
        return f.read()


def chown_files_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            os.chown(os.path.abspath(os.path.join(root, f)),
                     int(os.environ['host_uid']), int(os.environ['host_gid']))
        break   # do not traverse recursively


def check_file_appearance_rate(folder: str = 'results/serialized/', interval_length: int = 60*60):
    """
    Logs out the rate of file appearance within a given folder. Could be useful when running benchmark to see how many
        Experiments were performed hourly / daily since startup. Does not traverses recursively.

    :param folder: (str). Folder with files of interest.
    :param interval_length: (int). Time interval within number of files are aggregating.
    :return: None
    """
    previous_logging_level = logging.getLogger().level
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    files = os.listdir(folder)
    files_and_date = dict((file, os.path.getmtime(folder + file)) for file in files)

    files.sort(key=lambda filename: files_and_date[filename])
    first_file_creation_time = files_and_date[files[0]]
    curtime = time.time()

    for time_interval in range(int(first_file_creation_time), int(curtime), interval_length):
        counter = 0
        while files and files_and_date[files[0]] < time_interval + interval_length:
            counter += 1
            files.pop(0)
        logger.info(" " + time.ctime(time_interval) + " |->| " + time.ctime(time_interval + interval_length) + ': Runned %s experiments.' % counter)

    logging.basicConfig(level=previous_logging_level)


class MainAPIClient:
    def __init__(self, api_address: str = 'http://localhost:49152', dump_storage: str = "./results/serialized"):

        self.logger = logging.getLogger(__name__)
        if self._check_remote_socket_availability(api_address):
            self.main_api_address = api_address
        else:
            raise ValueError("Main node HTTP API is not available at %s" % api_address)
        self.dump_storage = dump_storage
        logger_for_sockets = logging.getLogger("SocketIOClient")
        logger_for_engineio = logging.getLogger("EngineIO")
        logger_for_sockets.setLevel(logging.WARNING)
        logger_for_engineio.setLevel(logging.WARNING)
        self.socket_client = socketio.Client(logger=logger_for_sockets, engineio_logger=logger_for_engineio)
        self.socket_client.on("final", self.download_latest_dump, namespace='/')
        self.isBusy = True
        self._connect_if_needed()

    def __del__(self):
        if "socket_client" in self.__dict__.keys():
            self.socket_client.disconnect()

    def _connect_if_needed(self):
        while not self.socket_client.eio.sid:
            self.logger.debug("Connecting to the main node API at %s" % self.main_api_address)
            self.socket_client.connect(self.main_api_address)
            if not self.socket_client.eio.sid:
                self.logger.warning("Unable to connect to main node API at %s." % self.main_api_address)
                self.socket_client.sleep(5)

    # --- HTTP API commands ---
    def _send_get_request(self, url: str):
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("%s RESPONSE FOR GET: %s -> %s" %
                            response.status_code, response.request.path_url, response.text)
        else:
            self.logger.debug(url + "|->|" + response.text)
            return response.text

    def _send_post_request(self, url: str, json_payload: dict):
        response = requests.post(url=url, json=json_payload)
        if response.status_code != 200:
            raise Exception("%s RESPONSE FOR POST: %s, %s -> %s" %
                            response.status_code, response.request.path_url, response.request.body, response.text)
        else:
            self.logger.debug(url + "|->|" + response.text)
            return response.text

    def update_status(self):
        status_report = json.loads(self._send_get_request(self.main_api_address + '/status'))
        self.isBusy = status_report['MAIN_PROCESS']['main process']
        return json.loads(self._send_get_request(self.main_api_address + '/status'))

    def start_main(self, experiment_description: dict = None):
        if experiment_description is None:
            response = self._send_get_request(self.main_api_address + '/main_start')
        else:
            response = self._send_post_request(self.main_api_address + '/main_start', json_payload=experiment_description)
        return json.loads(response)

    def stop_main(self):
        return json.loads(self._send_get_request(self.main_api_address + '/main_stop'))

    def download_latest_dump(self, *args, **kwargs):
        if not os.path.exists(self.dump_storage):
            os.makedirs(self.dump_storage)

        response = requests.get(self.main_api_address + '/download_dump/pkl')

        # Parsing the name of stored dump in main-node
        file_name = re.findall('filename=(.+)', response.headers.get('content-disposition'))[0]

        # Unique name for a dump
        full_file_name = self.dump_storage + file_name
        backup_counter = 0
        while os.path.exists(full_file_name):
            file_name = file_name[:file_name.rfind(".")] + "({0})".format(backup_counter) + file_name[file_name.rfind("."):]
            full_file_name = self.dump_storage + file_name
            backup_counter += 1

        # Store the Experiment dump
        with open(full_file_name, 'wb') as f:
            f.write(response.content)

        self.update_status()

    @staticmethod
    def _check_remote_socket_availability(address: Union[str, tuple]):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        # is_not_available return value is Int (exit code). 0 - if all is ok (available).
        try:
            if type(address) == str:
                sock.connect((address.split(':')[1][2:], int(address.split(':')[2])))
            else:   # address = (Hostname(str), port(int))
                sock.connect(address)
            sock.close()
            is_available = True
        except Exception as e:
            is_available = False
            logging.error("Connection to %s failed: %s" % (address, e))
        finally:
            return is_available

    # --- General out-of-box methods ---
    def perform_experiment(self, experiment_description: dict = None, wait_for_results: Union[bool, float] = 20 * 60):
        """
            Send the Experiment Description to the Main node and start the Experiment.

        :param experiment_description: Dict. Experiment Description that will be sent to the Main node.

        :param wait_for_results: If ``False`` - client will only send an Experiment Description and return response with
                                the Main node status.

                                If ``True`` was specified - client will wait until the end of the Experiment.

                                If numeric value were specified - client will wait specified amount of time (in
                                seconds), after elapsing - ``main_stop`` command will be sent to terminate the Main node.

        :return: (bool) Falase if unable to execute experiment or exectuion failed (becasuse of the Timeout).
                        True if experiment was executed properly or in case of async execution - experimen was accepted.
        """
        self._connect_if_needed()
        self.update_status()
        if self.isBusy:
            self.logger.error("Unable to perform an experiment, Main node is currently running an Experiment.")
            return False

        self.logger.info("Performing the Experiment: \n%s" % experiment_description)
        self.start_main(experiment_description)
        self.update_status()
        if type(wait_for_results) is bool and wait_for_results is False:
            if self.isBusy:
                self.logger.info("Experiment is running in async mode.")
                return True
            else:
                self.logger.error("Experiment is not running in async mode.")
                return False

        starting_time = datetime.datetime.now()

        while self.isBusy:  # will be changed in a callback for "final" event - download_latest_dump.
            if bool is not type(wait_for_results):
                if (datetime.datetime.now() - starting_time).seconds > wait_for_results:
                    self.logger.error("Unable to finish Experiment in time. Terminating.")
                    self.stop_main()
                    return False
            self.socket_client.sleep(1)
            self._connect_if_needed()
            continue

        return True


if __name__ == "__main__":
    check_file_appearance_rate()
