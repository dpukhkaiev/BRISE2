import base64
import sys
import pickle
import random
import uuid
from threading import Thread

import pika
import datetime
import logging
import json
import time
import os
from typing import Union
from string import ascii_lowercase

import plotly.io as pio

sys.path.append('/app')
from core_entities.search_space import SearchSpace

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


def restore(*args, workdir: str = "./results/serialized/", **kwargs):
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


def export_plot(plot: dict, wight: int = 600, height: int = 400, path: str = './results/reports/',
                file_format: str = '.svg'):
    """ Export plot in another format. Support vector and raster - svg, pdf, png, jpg, webp.

    Args:
        plot (Plotly dictionary): Layout of plot with data
        wight (int, optional): Wight of output image. Defaults to 600.
        height (int, optional): Height of output image. Defaults to 400.
        path (str, optional): Path to export the file. Defaults to './results/reports/'.
        file_format (str, optional): Export file format. Defaults to '.svg'.
    """
    name = ''.join(random.choice(ascii_lowercase) for _ in range(10)) + file_format
    pio.write_image(plot, path + name, width=wight, height=height)


def get_resource_as_string(name: str, charset: str = 'utf-8'):
    with open(name, "r", encoding=charset) as f:
        return f.read()


def chown_files_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            os.chown(os.path.abspath(os.path.join(root, f)),
                     int(os.environ['host_uid']), int(os.environ['host_gid']))
        break  # do not traverse recursively


def check_file_appearance_rate(folder: str = 'results/serialized/', interval_length: int = 60 * 60):
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
        logger.info(" " + time.ctime(time_interval) + " |->| " + time.ctime(
            time_interval + interval_length) + ': Runned %s experiments.' % counter)

    logging.basicConfig(level=previous_logging_level)


class MainAPIClient:
    class ConsumerThread(Thread):
        """
           This class runs in a separate thread and handles final event from the main node,'
            connected to the `benchmark_final_queue` as a consumer,
            downloads a latest dump file and changes main_client.isBusy to False
           """

        def __init__(self, host: str, port: int, main_client, *args, **kwargs):
            super(MainAPIClient.ConsumerThread, self).__init__(*args, **kwargs)

            self._host = host
            self._port = port
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
            self.consume_channel = self.connection.channel()
            self.consume_channel.basic_consume(queue='benchmark_final_queue', auto_ack=False,
                                               on_message_callback=self.final_event)
            self._is_interrupted = False
            self.main_client = main_client

        def final_event(self, ch: pika.spec.Channel, method: pika.spec.methods, properties: pika.spec.BasicProperties,
                        body: bytes):
            """
            Function for handling a final event that comes from the main node
            :param ch: pika.spec.Channel
            :param method:  pika.spec.Basic.GetOk
            :param properties: pika.spec.BasicProperties
            :param body: result of a configurations in bytes format
            """
            self.main_client.download_latest_dump()
            self.main_client.isBusy = False
            self.consume_channel.basic_ack(delivery_tag=method.delivery_tag)

        def run(self):
            """
            Point of entry to final event consumer functionality, listening of the queue with final events
            """
            try:
                while self.consume_channel._consumer_infos:
                    self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
                    if self._is_interrupted:
                        if self.connection.is_open:
                            self.connection.close()
                        break
            finally:
                if self.connection.is_open:
                    self.connection.close()

        def stop(self):
            self._is_interrupted = True

    def __init__(self, host_event_service: str, port_event_service: int, dump_storage: str = "./results/serialized"):

        self.logger = logging.getLogger(__name__)
        self.dump_storage = dump_storage

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host_event_service, port=port_event_service))

        self.channel = self.connection.channel()

        self.channel.basic_consume(
            queue="main_responses",
            on_message_callback=self.on_response,
            auto_ack=True)
        self.customer_thread = self.ConsumerThread('event_service', 49153, self)
        self.customer_thread.start()
        self.response = None
        self.corr_id = None

    def on_response(self, ch: pika.spec.Channel, method: pika.spec.methods, properties: pika.spec.BasicProperties,
                    body: bytes):
        """
        Call back function for RPC `call` function
        :param ch: pika.spec.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of a configurations in bytes format
        """
        if self.corr_id == properties.correlation_id:
            self.response = json.loads(body)

    def call(self, action: str, param: str = ""):
        """
        RPC function
        :param action: action on the main node:
            - start: to start the main script
            - status: to get the status of the main process
            - stop: to stop the main script
            - download_dump: to download dump file
        :param param: body for a specific action. See details in specific action in main-node/api-supreme.py
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(
            exchange='',
            routing_key=f'main_{action}_queue',
            properties=pika.BasicProperties(
                reply_to="main_responses",
                correlation_id=self.corr_id,
                headers={'body_type': 'pickle'}
            ),
            body=param)

        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def update_status(self):
        status_report = self.call("status")
        self.isBusy = status_report['MAIN_PROCESS']['main process']
        return status_report

    def start_main(self, experiment_description: dict, search_space: SearchSpace):
        data = pickle.dumps(
            {"experiment_description": experiment_description,
             "search_space": search_space}
        )
        response = self.call("start", param=data)

        return response

    def stop_main(self):
        return self.call("stop")

    def stop_client(self):
        self.customer_thread.stop()

    def download_latest_dump(self, *args, **kwargs):
        if not os.path.exists(self.dump_storage):
            os.makedirs(self.dump_storage)
        param = {}
        param['format'] = 'pkl'
        response = self.call("download_dump", json.dumps(param))
        if response["status"] == "ok":
            # Parsing the name of stored dump in main-node
            file_name = response["file_name"]
            body = base64.b64decode(response["body"])
            # Unique name for a dump
            full_file_name = self.dump_storage + file_name
            backup_counter = 0
            while os.path.exists(full_file_name):
                file_name = file_name[:file_name.rfind(".")] + "({0})".format(backup_counter) + file_name[
                                                                                                file_name.rfind("."):]
                full_file_name = self.dump_storage + file_name
                backup_counter += 1

            # Store the Experiment dump
            with open(full_file_name, 'wb') as f:
                f.write(body)
        else:
            self.logger.error(response["status"])

        self.update_status()

    # --- General out-of-box methods ---
    def perform_experiment(self, experiment_description: dict = None, search_space: SearchSpace = None,
                           wait_for_results: Union[bool, float] = 20 * 60):
        """
            Send the Experiment Description to the Main node and start the Experiment.

        :param experiment_description: Dict. Experiment Description that will be sent to the Main node.

        :param search_space: SearchSpace object. Information about search space that will be sent to the Main node.

        :param wait_for_results: If ``False`` - client will only send an Experiment Description and return response with
                                the Main node status.

                                If ``True`` was specified - client will wait until the end of the Experiment.

                                If numeric value were specified - client will wait specified amount of time (in
                                seconds), after elapsing - ``main_stop`` command will be sent to terminate the Main node.

        :return: (bool) Falase if unable to execute experiment or exectuion failed (becasuse of the Timeout).
                        True if experiment was executed properly or in case of async execution - experimen was accepted.
        """
        self.update_status()
        if self.isBusy:
            self.logger.error("Unable to perform an experiment, Main node is currently running an Experiment.")
            return False

        self.logger.info("Performing the Experiment: \n%s" % experiment_description)
        self.start_main(experiment_description, search_space)
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
            continue
        return True


if __name__ == "__main__":
    check_file_appearance_rate()
