import base64
import datetime
import glob
import hashlib
import json
import logging
import os
import pickle
import shutil
import uuid
from copy import deepcopy
from functools import wraps
from threading import Thread
from typing import Union

import numpy as np
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
        os.sys.argv.pop()  # Because load_experiment_description will consider 'benchmark' as Experiment Description.
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
        Decorator that enables a pre-calculation of a number of experiments in implemented benchmark scenario
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
                "Benchmark is going to run %s unique Experiments (please, take into account the repetitions as well)."
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
         :param search_space: Hyperparameter. Initialized Hyperparameter object.
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
    def benchmark_test(self):
        """
        This is an EXAMPLE of a benchmark scenario, utilized for testing purposes.
        While benchmarking BRISE, one would like to see the influence of changing its product configuration on the
            overall process of running BRISE, on the results quality and on the effort.

            In this particular example, the benchmark described in following way:
                1. Using base Experiment Description from the test suite.
                2. Changing ONE feature at a time.
                    2.1. For each Transfer Learning type.
                    2.2. For each Target System Scenario (test_#).
                3. Execute BRISE with this changed Experiment Description 3 times and save Experiment dump after
                    each execution.

            Do not forget to call your benchmarking scenario in a code block of the `run_benchmark` function,
            highlighted by
            # ---    Add User defined benchmark scenarios execution below

            :return: int, number of Experiments that were executed and experiment dumps are stored.
            """
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_0.json")
        self._experiment_timeout = 5 * 60
        basic_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {
                            "Infinite": {
                                "Value": np.inf
                            }
                        },
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {}
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Hard",
                        "TimeToBuildModelThreshold": 0.5,
                        "TimeUnit": "seconds"
                    }
                },
                "MultiTaskLearning": {
                    "Filters": {
                        "OnlyBestConfigurations": {
                            "Type": "only_best"
                        }
                    }
                }
            }
        }
        clustering_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "AdaptiveQuantity": {
                                "Clustering": {
                                    "MeanShift": {
                                        "Type": "mean_shift_clustering",
                                        "BandwidthType": "Fixed",
                                        "bandwidth": 0.3,
                                        "quantile": 0.3
                                    }
                                }
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {
                            "Infinite": {
                                "Value": np.inf
                            }
                        },
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {}
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Hard",
                        "TimeToBuildModelThreshold": 0.5,
                        "TimeUnit": "seconds"
                    }
                },
                "MultiTaskLearning": {
                    "Filters": {
                        "OnlyBestConfigurations": {
                            "Type": "only_best"
                        }
                    }
                }
            }
        }
        no_tl_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 1,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                }
            }
        }
        mr_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {
                            "Infinite": {
                                "Value": np.inf
                            }
                        },
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {}
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Hard",
                        "TimeToBuildModelThreshold": 0.5,
                        "TimeUnit": "seconds"
                    }
                }
            }
        }
        mr_skeleton_finite_granularity = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {
                            "Finite": {
                                "Value": 1
                            }
                        },
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {}
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Hard",
                        "TimeToBuildModelThreshold": 0.5,
                        "TimeUnit": "seconds"
                    }
                }
            }
        }
        mtl_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "MultiTaskLearning": {
                    "Filters": {
                        "OnlyBestConfigurations": {
                            "Type": "only_best"
                        },
                        "OldNewRatio": {
                            "Type": "old_new_ratio",
                            "OldNewConfigsRatio": 0.5
                        }
                    }
                }
            }
        }
        experiment_description = self.base_experiment_description

        # benchmarking basic tl setting
        for num_samples in range(1, 10):
            experiment_description['TransferLearning']['TransferExpediencyDetermination']["SamplingLandmarkBased"][
                "MinNumberOfSamples"] = num_samples
            self.execute_experiment(experiment_description)

        # benchmarking no tl setting
        experiment_description.update(deepcopy(no_tl_skeleton))
        self.execute_experiment(experiment_description)

        # benchmarking mr
        for time_to_build_threshold in [0.1, 0.2, 0.3, 0.4, 0.5, 1.0]:
            experiment_description.update(deepcopy(mr_skeleton))
            experiment_description['TransferLearning']['ModelRecommendation']['DynamicModelsRecommendation'][
                'TimeToBuildModelThreshold'] = time_to_build_threshold
            self.execute_experiment(experiment_description)

        for recommendation_granularity in [1, 5, 10, 20, 30, 50]:
            experiment_description.update(deepcopy(mr_skeleton_finite_granularity))
            experiment_description['TransferLearning']['ModelRecommendation']['DynamicModelsRecommendation'][
                'RecommendationGranularity']['Finite']['Value'] = recommendation_granularity
            self.execute_experiment(experiment_description)

        # benchmarking mtl
        for old_new_configs_ratio in [0.1, 0.2, 0.3, 0.4, 0.5, 1.0]:
            experiment_description.update(deepcopy(mtl_skeleton))
            experiment_description['TransferLearning']['MultiTaskLearning']['Filters']['OldNewRatio'][
                'OldNewConfigsRatio'] = old_new_configs_ratio
            self.execute_experiment(experiment_description)

        return self.counter

    @_benchmarkable
    def fill_db(self):
        self._experiment_timeout = 5 * 60
        time_based_sc_skeleton = {
            "StopCondition": {
                "Instance": {
                    "TimeBasedSC": {
                        "Parameters": {
                            "MaxRunTime": 1,
                            "TimeUnit": "minutes"
                        },
                        "Type": "time_based",
                        "Name": "t"
                    }
                },
                "StopConditionTriggerLogic": {
                    "Expression": "t",
                    "InspectionParameters": {
                        "RepetitionPeriod": 1,
                        "TimeUnit": "seconds"
                    }
                }
            }
        }
        flat_2float_model_skeleton = {
            "ConfigurationSelection": {
                "SamplingStrategy": {
                    "Sobol": {
                        "Seed": 1,
                        "Type": "sobol"
                    }
                },
                "Predictor": {
                    "WindowSize": 1.0,
                    "Model": {
                        "Surrogate": {
                            "ConfigurationTransformers": {
                                "FloatTransformer": {
                                    "SklearnFloatMinMaxScaler": {
                                        "Type": "sklearn_float_transformer",
                                        "Class": "sklearn.MinMaxScaler"
                                    }
                                }
                            },
                            "Instance": {
                                "GaussianProcessRegressor": {
                                    "MultiObjective": "True",
                                    "Parameters": {
                                        "n_restarts_optimizer": 4
                                    },
                                    "Type": "sklearn_model_wrapper",
                                    "Class": "sklearn.gaussian_process.GaussianProcessRegressor"
                                }
                            }
                        },
                        "Optimizer": {
                            "ConfigurationTransformers": {
                                "FloatTransformer": {
                                    "SklearnFloatMinMaxScaler": {
                                        "Type": "sklearn_float_transformer",
                                        "Class": "sklearn.MinMaxScaler"
                                    }
                                }
                            },
                            "Instance": {
                                "MOEA": {
                                    "Generations": 10,
                                    "PopulationSize": 100,
                                    "Algorithms": {
                                        "GACO": {}
                                    },
                                    "Type": "moea"
                                }
                            }
                        },
                        "Validator": {
                            "ExternalValidator": {
                                "MockValidator": {
                                    "Type": "mock_validator"
                                }
                            }
                        },
                        "CandidateSelector": {
                            "BestMultiPointProposal": {
                                "NumberOfPoints": 1,
                                "Type": "best_multi_point"
                            }
                        }
                    }
                }
            }
        }
        flat_float_nom_model_skeleton = {
            "ConfigurationSelection": {
                "SamplingStrategy": {
                    "Sobol": {
                        "Seed": 1,
                        "Type": "sobol"
                    }
                },
                "Predictor": {
                    "WindowSize": 1.0,
                    "Model": {
                        "Surrogate": {
                            "ConfigurationTransformers": {
                                "NominalTransformer": {
                                    "SklearnBinaryTransformer": {
                                        "Type": "sklearn_binary_transformer",
                                        "Class": "sklearn.OrdinalEncoder"
                                    }
                                }
                            },
                            "Instance": {
                                "GaussianProcessRegressor": {
                                    "MultiObjective": "True",
                                    "Parameters": {
                                        "n_restarts_optimizer": 4
                                    },
                                    "Type": "sklearn_model_wrapper",
                                    "Class": "sklearn.gaussian_process.GaussianProcessRegressor"
                                }
                            }
                        },
                        "Optimizer": {
                            "ConfigurationTransformers": {
                                "NominalTransformer": {
                                    "SklearnBinaryTransformer": {
                                        "Type": "sklearn_binary_transformer",
                                        "Class": "sklearn.OrdinalEncoder"
                                    }
                                }
                            },
                            "Instance": {
                                "MOEA": {
                                    "Generations": 10,
                                    "PopulationSize": 100,
                                    "Algorithms": {
                                        "GACO": {}
                                    },
                                    "Type": "moea"
                                }
                            }
                        },
                        "Validator": {
                            "ExternalValidator": {
                                "MockValidator": {
                                    "Type": "mock_validator"
                                }
                            }
                        },
                        "CandidateSelector": {
                            "BestMultiPointProposal": {
                                "NumberOfPoints": 1,
                                "Type": "best_multi_point"
                            }
                        }
                    }
                }
            }
        }
        # test case with 2 float parameters
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_0.json")
        experiment_description = self.base_experiment_description
        experiment_description.update(deepcopy(time_based_sc_skeleton))
        experiment_description.update(deepcopy(flat_2float_model_skeleton))
        self.execute_experiment(experiment_description, number_of_repetitions=1)

        # test case with float nom parameters
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_4.json")
        experiment_description = self.base_experiment_description
        experiment_description.update(deepcopy(time_based_sc_skeleton))
        experiment_description.update(deepcopy(flat_float_nom_model_skeleton))
        self.execute_experiment(experiment_description, number_of_repetitions=1)

        # test case with float nom parameters and random DCH
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_9.json")
        experiment_description = self.base_experiment_description
        experiment_description.update(deepcopy(time_based_sc_skeleton))
        experiment_description.update(deepcopy(flat_float_nom_model_skeleton))
        self.execute_experiment(experiment_description, number_of_repetitions=1)

        # test case with all parameter types and random DCH
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_2.json")
        experiment_description = self.base_experiment_description
        experiment_description.update(deepcopy(time_based_sc_skeleton))
        self.execute_experiment(experiment_description, number_of_repetitions=1)

        # test case with all parameter types
        self._base_experiment_description, self._base_search_space = \
            load_experiment_setup("./Resources/test/test_cases_product_configurations/test_case_2_wo_dch.json")
        experiment_description = self.base_experiment_description
        experiment_description.update(deepcopy(time_based_sc_skeleton))
        self.execute_experiment(experiment_description, number_of_repetitions=1)

        return self.counter


class MainAPIClient:
    class ConsumerThread(Thread):
        """
           This class runs in a separate thread and handles the final event from the main node,'
            connected to the `benchmark_final_queue` as a consumer,
            downloads the last dump file and changes main_client.isBusy to False
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
        :param param: body for a specific action. See details in specific action in main_node/api-supreme.py
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
            {"metric_description": experiment_description,
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
            file_name = file_name[file_name[:file_name.rfind(".")].rfind("/") + 1:]
            body = base64.b64decode(response["body"])
            # Unique name for a dump
            full_file_name = self.dump_storage + file_name
            backup_counter = 0
            while os.path.exists(full_file_name):
                file_name = file_name[file_name[:file_name.rfind(".")].rfind("/") + 1:] \
                    + "({0})".format(backup_counter) + file_name[file_name.rfind("."):]
                full_file_name = self.dump_storage + file_name
                backup_counter += 1

            # Store the Experiment dump
            with open(full_file_name, 'wb') as f:
                f.write(body)
        else:
            self.logger.error(response["status"])

        self.update_status()

    # --- General methods ---
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

        :return: (bool) False if unable to execute experiment or execution failed (because of the Timeout).
                        True if experiment was executed properly or in case of async execution - experiment was accepted.
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
