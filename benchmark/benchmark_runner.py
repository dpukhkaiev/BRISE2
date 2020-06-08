import os
import uuid
import json
import glob
import pickle
import shutil
import base64
import hashlib
import logging
import datetime
from typing import Union
from copy import deepcopy
from functools import wraps
from threading import Thread

import pika

from core_entities.search_space import SearchSpace
from tools.initial_config import load_experiment_setup


class BRISEBenchmarkRunner:
    """
       Class for building and running the benchmarking scenarios.
    """

    def __init__(self, host_event_service: str, port_event_service: int, results_storage: str):
        """
            Initializes benchmarking client.
        :param host_event_service: str. URL of event service. For example "http://main-node:49152"
        :param port_event_service: str. access port of event service
        :param results_storage: str. Folder where to store benchmark results (dump files of experiments).
        """
        os.sys.argv.pop()  # Because load_experiment_description will consider 'benchmark' as Experiment Description).
        self._base_experiment_description = None
        self._base_search_space = None
        self._experiment_timeout = float('inf')
        self.results_storage = results_storage if results_storage[-1] == "/" else results_storage + "/"
        self.main_api_client = MainAPIClient(host_event_service, port_event_service, results_storage)
        self.logger = logging.getLogger(__name__)
        self.counter = 1
        self.experiments_to_be_performed = []   # List of experiment IDs
        self.is_calculating_number_of_experiments = False

    @property
    def base_experiment_description(self):
        return deepcopy(self._base_experiment_description)

    @base_experiment_description.setter
    def base_experiment_description(self, description):
        if not self._base_experiment_description:
            self._base_experiment_description = deepcopy(description)
        else:
            self.logger.error("Unable to update Experiment Description: Read-only property.")

    def _benchmarkable(benchmarking_function):
        """
            Decorator that enables a pre calculation of a number of experiments in implemented benchmark scenario
            without actually running them. It is not essential for benchmarking, but could be useful.
            NOTE: This method should be used ONLY as a decorator for other BRISEBenchmark object methods!
        :return: original function, wrapped by wrapper.
        """
        @wraps(benchmarking_function)
        def wrapper(self, *args, **kwargs):
            logging.info("Calculating number of Experiments to perform during benchmark.")
            self.is_calculating_number_of_experiments = True
            logging_level = self.logger.level
            self.logger.setLevel(logging.WARNING)
            benchmarking_function(self, *args, *kwargs)
            self.logger.setLevel(logging_level)
            logging.info(
                "Benchmark is going to run %s unique Experiments (please, take into account also the repetitions)."
                % len(self.experiments_to_be_performed))
            self.is_calculating_number_of_experiments = False
            benchmarking_function(self, *args, *kwargs)
        return wrapper

    def execute_experiment(self,
                           experiment_description: dict,
                           search_space: SearchSpace = None,
                           number_of_repetitions: int = 3):
        """
             Check how many dumps are available for particular Experiment Description.

         :param experiment_description: Dict. Experiment Description
         :param search_space: SearchSpace. Initialized SearchSpace object.
         :param number_of_repetitions: int. number of times to execute the same Experiment.

         :return: int. Number of times experiment dump was found in a storage.
        """
        experiment_id = hashlib.sha1(json.dumps(experiment_description, sort_keys=True).encode("utf-8")).hexdigest()
        search_space = search_space if search_space else self._base_search_space

        number_of_available_repetitions = sum(experiment_id in file for file in os.listdir(self.results_storage))
        need_to_execute = max(number_of_repetitions - number_of_available_repetitions, 0)

        if self.is_calculating_number_of_experiments:
            self.experiments_to_be_performed.extend([experiment_id] * need_to_execute)
        else:
            self.counter += number_of_available_repetitions
            while number_of_available_repetitions < number_of_repetitions:
                self.logger.info(f"Executing Experiment #{self.counter} out of "
                                 f"{len(self.experiments_to_be_performed) * number_of_repetitions}. "
                                 f"ID: {experiment_id}. Repetition: {number_of_available_repetitions}.")
                if self.main_api_client.perform_experiment(experiment_description,
                                                           search_space,
                                                           wait_for_results=self._experiment_timeout):
                    number_of_available_repetitions += 1
                    self.counter += 1
            return number_of_repetitions

    def move_redundant_experiments(self, location: str):
        """
            Move all experiment dumps that are not part of current benchmark to separate 'location' folder.
        :param location: (str). Folder path where redundant experiment dumps will be stored.
        """
        os.makedirs(location, exist_ok=True)

        # Mark what to move
        redundant_experiment_files = glob.glob(self.results_storage + "*.pkl")
        for experiment_id in self.experiments_to_be_performed:
            for file in redundant_experiment_files:
                if experiment_id in file:
                    redundant_experiment_files.remove(file)

        # Move
        for file in redundant_experiment_files:
            shutil.move(file, location + os.path.basename(file))

    @_benchmarkable
    def benchmark_repeater(self):
        """
            This is an EXAMPLE of the benchmark scenario.

            NOTE: This benchmark based on Energy Consupmtion Experiments, those to run this benchmark,
             one should add files Experiment scenario files:
                - 'scenarios/energy_consumption/search_space_96' for Search Space with 96 points,
                - 'scenarios/energy_consumption/search_space_512' for Search Space with 512 points respectively.

            HINT: Add following COPY commands to Dockerfile of benchmark container under the line
            # -     add your information here   -
            ```
            COPY ./worker/scenarios/energy_consumption/search_space_96/*full.csv /home/benchmark_user/scenarios/energy_consumption/search_space_96/
            COPY ./worker/scenarios/energy_consumption/search_space_512/*full.csv /home/benchmark_user/scenarios/energy_consumption/search_space_512/
            ```

            While benchmarking BRISE, one would like to see the influence of changing some particular parameters on the
            overall process of running BRISE, on the results quality and on the effort.

            In this particular example, the Repeater benchmark described in following way:
                1. Using base Experiment Description for Energy Consumption.
                2. Change ONE parameter of Repeater in a time.
                    2.1. For each Repeater type (Default, Student and Student with enabled experiment-awareness).
                    2.2. For each Target System Scenario (ws_file).
                3. Execute BRISE with this changed Experiment Description 3 times and save Experiment dump after
                    each execution.

            Do not forget to call your benchmarking scenario in a code block of the `run_benchmark` function,
            highlighted by
            # ---    Add User defined benchmark scenarios execution below

        :return: int, number of Experiments that were executed and experiment dumps are stored.
                Actually you could return whatever you want, here this number is returned only for reporting purposes.
        """
        self._base_experiment_description, self._base_search_space = load_experiment_setup("./Resources/EnergyExperiment.json")
        self._experiment_timeout = 5 * 60

        quality_based_repeater_skeleton = {
            "Repeater": {
                "Type": "QuantityBased",
                "Parameters": {
                    "MaxFailedTasksPerConfiguration": 5,
                    "MaxTasksPerConfiguration": 10
                }
            }
        }

        acceptable_error_based_repeater_skeleton = {
            "Repeater": {
                "Type": "AcceptableErrorBased",
                "Parameters": {
                    "ExperimentAwareness": {
                        "MaxAcceptableErrors": [50],
                        "RatiosMax": [3],
                        "isEnabled": True
                    },
                    "MaxFailedTasksPerConfiguration": 5,
                    "MaxTasksPerConfiguration": 10,
                    "MinTasksPerConfiguration": 2,
                    "DevicesScaleAccuracies": [0],
                    "BaseAcceptableErrors": [5],
                    "DevicesAccuracyClasses": [0],
                    "ConfidenceLevels": [0.95]
                }
            }
        }

        csv_files = os.listdir('scenarios/energy_consumption/search_space_96')

        # There exist also a scenario with search space of 512 points,
        # but one need to use also EnergyExperimentData(512points).json instead of regular EnergyExperimentData.json
        # csv_files = ["scenarios/energy_consumption/search_space_512/pigz_cr_audio1.wav_compress_full.csv"]

        for idx, ws_file in enumerate(csv_files):
            experiment_description = self.base_experiment_description
            experiment_description['TaskConfiguration']['Scenario']['ws_file'] = "search_space_96/" + ws_file
            self.logger.info(f"Benchmarking next Scenario file(ws_file): "
                             f"search_space_96/{ws_file} ({idx} out of {len(csv_files)}).")

            # benchmarking a quantity-based repeater
            for max_repeat in range(1, 11):
                experiment_description.update(deepcopy(quality_based_repeater_skeleton))
                experiment_description['Repeater']['Parameters']["MaxTasksPerConfiguration"] = max_repeat
                self.execute_experiment(experiment_description)

            # benchmarking a quantity-based repeater with an extended number of repetitions
            for max_repeat in [20, 30, 40, 50]:
                experiment_description.update(deepcopy(quality_based_repeater_skeleton))
                experiment_description['Repeater']['Parameters']["MaxTasksPerConfiguration"] = max_repeat
                self.execute_experiment(experiment_description)

            # benchmarking an acceptable-error-based repeater with disabled experiment-awareness
            experiment_description.update(deepcopy(acceptable_error_based_repeater_skeleton))
            experiment_description['Repeater']['Parameters']['ExperimentAwareness']["isEnabled"] = False
            # different MaxTasksPerConfiguration
            for MaxTasksPerConfiguration in [10, 50]:
                experiment_description['Repeater']['Parameters']['MaxTasksPerConfiguration'] = MaxTasksPerConfiguration
                for BaseAcceptableErrors in [1, 5, 10, 25, 50]:
                    experiment_description['Repeater']['Parameters']['BaseAcceptableErrors'] = [BaseAcceptableErrors]
                    self.logger.info("Acceptable-error-based Repeater, MaxTasksPerConfiguration %s: "
                                     "Changing BaseAcceptableErrors to %s"
                                     % (MaxTasksPerConfiguration, BaseAcceptableErrors))
                    self.execute_experiment(experiment_description)

            # benchmarking an acceptable-error-based repeater with enabled experiment-awareness
            experiment_description.update(deepcopy(acceptable_error_based_repeater_skeleton))
            for BaseAcceptableErrors in [1, 5, 10, 25, 50]:
                experiment_description['Repeater']['Parameters']['BaseAcceptableErrors'] = [BaseAcceptableErrors]
                self.logger.info("Experiment-aware acceptable-error-based Repeater: Changing BaseAcceptableErrors to %s" % BaseAcceptableErrors)
                self.execute_experiment(experiment_description)

            experiment_description.update(deepcopy(acceptable_error_based_repeater_skeleton))
            for MaxAcceptableErrors in [25, 50, 75]:
                experiment_description['Repeater']['Parameters']['ExperimentAwareness']['MaxAcceptableErrors'] = [
                    MaxAcceptableErrors]
                self.logger.info("Experiment-aware acceptable-error-based Repeater: Changing MaxAcceptableErrors to %s" % MaxAcceptableErrors)
                self.execute_experiment(experiment_description)

            experiment_description.update(deepcopy(acceptable_error_based_repeater_skeleton))
            for RatiosMax in [2, 3, 5, 10, 25]:
                experiment_description['Repeater']['Parameters']['ExperimentAwareness']['RatiosMax'] = [RatiosMax]
                self.logger.info("Experiment-aware acceptable-error-based Repeater: Changing RatiosMax to %s" % RatiosMax)
                self.execute_experiment(experiment_description)

        return self.counter

    def benchmark_SA(self):
        self._base_experiment_description, self._base_search_space = load_experiment_setup("./Resources/SA/SAExperiment.json")

        scenarios = {
          "trivial": { "variants": 1, "requests": 1, "depth": 1, "resources": 1.0 },
          "small": { "variants": 2, "requests": 1, "depth": 2, "resources": 1.5 },
          "small_hw": { "variants": 2, "requests": 1, "depth": 2, "resources": 5.0 },
          "small_sw": { "variants": 2, "requests": 1, "depth": 5, "resources": 1.5 },
          "medium": { "variants": 10, "requests": 15, "depth": 2, "resources": 1.5 },
          "medium_hw": { "variants": 10, "requests": 15, "depth": 2, "resources": 5.0 },
          "medium_sw": { "variants": 5, "requests": 10, "depth": 5, "resources": 1.5 },
          "large": { "variants": 20, "requests": 20, "depth": 2, "resources": 1.5 },
          "large_hw": { "variants": 20, "requests": 20, "depth": 2, "resources": 5.0 },
          "large_sw": { "variants": 10, "requests": 20, "depth": 5, "resources": 1.5 },
          "huge": { "variants": 50, "requests": 50, "depth": 2, "resources": 1.5 },
          "huge_hw": { "variants": 50, "requests": 50, "depth": 2, "resources": 5.0 },
          "huge_sw": {"variants": 20, "requests": 50, "depth": 5, "resources": 1.5 }
        }

        for s in scenarios:
            self.logger.info("here")
            experiment_description = self.base_experiment_description
            experiment_description['TaskConfiguration']['Scenario']['ws_file'] = "result_v{}_q{}_d{}_r{}.csv".\
                format(scenarios[s]["variants"], scenarios[s]["requests"], scenarios[s]["depth"], str(scenarios[s]["resources"]).replace('.', '_'))
            experiment_description['TaskConfiguration']['Scenario']['numImplementations'] = scenarios[s]["variants"]
            experiment_description['TaskConfiguration']['Scenario']['numRequests'] = scenarios[s]["requests"]
            experiment_description['TaskConfiguration']['Scenario']['componentDepth'] = scenarios[s]["depth"]
            experiment_description['TaskConfiguration']['Scenario']['excessComputeResourceRatio'] = scenarios[s]["resources"]
            self.logger.info("Benchmarking next Scenario file(ws_file): %s" % experiment_description['TaskConfiguration']['Scenario']['ws_file'])
            self.execute_experiment(experiment_description)

        return self.counter


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
        self.customer_thread = self.ConsumerThread('event-service', 49153, self)
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

    def call(self, action: str, param: str = "") -> dict:
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
        param = {'format': 'pkl'}
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
