import time
import random
import os
import logging
import hashlib
import json
import glob
import shutil
import argparse
from string import ascii_lowercase
from functools import wraps
from copy import deepcopy
from jinja2 import Environment, FileSystemLoader
from plotly.offline import plot

# Tools
from shared_tools import restore, get_resource_as_string, MainAPIClient, chown_files_in_dir
# from shared_tools import export_plot
from tools.initial_config import load_experiment_description
from logger.default_logger import BRISELogConfigurator

# Plots
from plots.table import table
from plots.repeat_vs_avg import repeat_vs_avg
from plots.improvements import improvements
from plots.box_statistic import box_statistic
from plots.exp_config import exp_description_highlight

# Configuring logging
BRISELogConfigurator()


def build_benchmark_report():
    """ Generate report files from the Experiment class instances.
    """
    folder_with_dumps = './results/serialized/'
    # Container creation performs --volume on `./results/` folder. Change wisely folder_with_resport.
    folder_with_resport = './results/reports/'

    # ------- List with name experiment instances. Default from ./results/serialized/ folder
    experiment_dumps = [f for f in os.listdir(folder_with_dumps) if (f[-4:] == '.pkl')]
    # -------
    logger = logging.getLogger(__name__)
    if experiment_dumps:
        logger.info("Selected Experiment dumps for report: %s" % experiment_dumps)
    else:
        logger.error("Directory '%s' is empty. Terminating." % folder_with_dumps)
        return

    # --- Generate template
    file_loader = FileSystemLoader("./templates")
    env = Environment(loader=file_loader)
    env.globals['get_resource_as_string'] = get_resource_as_string
    template = env.get_template('index.html')

    # --- Restore experiments for benchmarking
    exp_list = restore(*experiment_dumps)

    # --- Generate plot's hooks
    tab = plot(table(exp_list), include_plotlyjs=False, output_type='div')
    impr = plot(improvements(exp_list),
                include_plotlyjs=False,
                output_type='div')
    all_results = plot(box_statistic(exp_list),
                       include_plotlyjs=False,
                       output_type='div')
    rep = ' '.join(plot(repeat_vs_avg(exp), include_plotlyjs=False,
                        output_type='div') for exp in exp_list)
    time_mark = time.strftime('%Y-%m-%d %A', time.localtime())

    # Compose HTML
    html = template.render(
        table=tab,
        impr=impr,
        repeat_vs_avg=rep,
        box_plot=all_results,
        time=time_mark,
        print_config=exp_description_highlight(exp_list)
    )

    # --- Save results
    # Write HTML report
    suffix = ''.join(random.choice(ascii_lowercase) for _ in range(10))
    with open("{}report_{}.html".format(folder_with_resport, suffix), "w", encoding='utf-8') as outf:
        outf.write(html)

    # # Export plots
    # for plt in [table(exp_list), improvements(exp_list), box_statistic(exp_list)]:
    #     export_plot(plot=plt, wight=1200, height=600)

    # Using a host machine User ID to change the owner for the files(initially, the owner was a root).
    chown_files_in_dir(folder_with_resport)


class BRISEBenchmark:
    """
       Class for building and running the benchmarking scenarios.
    """

    def __init__(self, main_api_addr: str, results_storage: str):
        """
            Initializes benchmarking client.
        :param main_api_addr: str. URL of main node API. For example "http://main-node:49152"
        :param results_storage: str. Folder where to store benchmark results (dump files of experiments).
        """
        os.sys.argv.pop()   # Because load_experiment_description will consider 'benchmark' as Experiment Description).
        self._base_experiment_description = load_experiment_description("./Resources/SA/SAExperiment.json")
        self.results_storage = results_storage if results_storage[-1] == "/" else results_storage  + "/"
        self.main_api_client = MainAPIClient(main_api_addr, dump_storage=results_storage)
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

    def benchmarkable(benchmarking_function):
        """
            Decorator that enables a pre calculation of a number of experiments in implemented benchmark scenario
            without actually running them. It is not essential for benchmarking, but could be useful.
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
            logging.info("Benchmark is going to run %s unique Experiments (please, take into account also the repetitions)."
                         % len(self.experiments_to_be_performed))
            self.is_calculating_number_of_experiments = False
            benchmarking_function(self, *args, *kwargs)
        return wrapper

    def execute_experiment(self, experiment_description: dict, number_of_repetitions: int = 3, wait_for_results: int=30*60):
        """
             Check how many dumps are available for particular Experiment Description.

         :param experiment_description: Dict. Experiment Description
         :param number_of_repetitions: int. number of times to execute the same Experiment.
         :param wait_for_results:
            If bool ``False`` - client will only send an Experiment Description and return response with
                                the Main node status.
            If bool ``True`` was specified - client will wait until the end of the Experiment.

            If numeric value (int or float) were specified - client will wait specified amount of time (in seconds),
            after elapsing - ``main_stop`` command will be sent to terminate the Main node, current state of Experiment
            will be reported be main node and saved by benchmark.

         :return: int. Number of times experiment dump was found in a storage.
        """
        experiment_id = hashlib.sha1(json.dumps(experiment_description, sort_keys=True).encode("utf-8")).hexdigest()
        dump_file_name = "exp_{0}_{1}".format(
            experiment_description['TaskConfiguration']['Scenario']["ws_file"], experiment_id)
        if self.is_calculating_number_of_experiments:
            self.experiments_to_be_performed.append(experiment_id)
        else:
            number_of_available_repetitions = sum(dump_file_name in file for file in os.listdir(self.results_storage))
            while number_of_available_repetitions < number_of_repetitions:
                if self.main_api_client.perform_experiment(experiment_description, wait_for_results=wait_for_results):
                    number_of_available_repetitions += 1
                    self.logger.info("Executed Experiment #{c} out of {m_c}. ID: {eid}. Repetition: {r}.".format(
                            c=self.counter,
                            m_c=len(self.experiments_to_be_performed) * number_of_repetitions,
                            eid=experiment_id,
                            r=number_of_available_repetitions
                        )
                    )
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


    @benchmarkable
    def benchmark_repeater(self):
        """
            This is an EXAMPLE of the benchmark scenario.

            While benchmarking BRISE, one would like to see the influence of changing some particular parameters on the
            overall process of running BRISE, on the results quality and on the effort.

            In this particular example, the Repeater benchmark described in following way:
                1. Using base Experiment Description for Energy Consumption.
                2. Change ONE parameter of Repeater in a time.
                    2.1. For each Repeater type (Default, Student and Student with enabled model-awareness).
                    2.2. For each Target System Scenario (ws_file).
                3. Execute BRISE with this changed Experiment Description 3 times and save Experiment dump after
                    each execution.

            Do not forget to call your benchmarking scenario in a code block of the `run_benchmark` function,
            highlighted by
            # ---    Add User defined benchmark scenarios execution below

        :return: int, number of Experiments that were executed and experiment dumps are stored.
                Actually you could return whatever you want, here this number is returned only for reporting purposes.
        """
        def_rep_skeleton = {"Repeater": {"Type": "default",
                                          "Parameters": {
                                              "MaxTasksPerConfiguration": 10}}}
        student_rep_skeleton = {"Repeater": {"Type": "student_deviation",
                                             "Parameters": {
                                                 "ModelAwareness": {
                                                     "MaxAcceptableErrors": [50],
                                                     "RatiosMax": [10],
                                                     "isEnabled": True
                                                 },
                                                 "MaxTasksPerConfiguration": 10,
                                                 "MinTasksPerConfiguration": 2,
                                                 "DevicesScaleAccuracies": [0],
                                                 "BaseAcceptableErrors": [5],
                                                 "DevicesAccuracyClasses": [0],
                                                 "ConfidenceLevels": [0.95]}}}

        for ws_file in os.listdir('scenarios/energy_consumption'):
            experiment_description = self.base_experiment_description
            experiment_description['TaskConfiguration']['Scenario']['ws_file'] = ws_file
            self.logger.info("Benchmarking next Scenario file(ws_file): %s" % ws_file)

            # benchmarking a default repeater
            experiment_description.update(deepcopy(def_rep_skeleton))
            self.execute_experiment(experiment_description)

            # benchmarking a student repeater with disabled model awareness
            experiment_description.update(deepcopy(student_rep_skeleton))
            experiment_description['Repeater']['Parameters']['ModelAwareness']["isEnabled"] = False
            for BaseAcceptableErrors in [5, 15, 50]:
                experiment_description['Repeater']['Parameters']['BaseAcceptableErrors'] = [BaseAcceptableErrors]
                self.logger.info("Default Repeater: Changing BaseAcceptableErrors to %s" % BaseAcceptableErrors)
                self.execute_experiment(experiment_description)

            # benchmarking a student repeater with enabled model awareness
            experiment_description.update(deepcopy(student_rep_skeleton))
            for BaseAcceptableErrors in [5, 15, 50]:
                experiment_description['Repeater']['Parameters']['BaseAcceptableErrors'] = [BaseAcceptableErrors]
                self.logger.info("Student Repeater: Changing BaseAcceptableErrors to %s" % BaseAcceptableErrors)
                self.execute_experiment(experiment_description)

            experiment_description.update(deepcopy(student_rep_skeleton))
            for MaxAcceptableErrors in [35, 50, 120]:
                experiment_description['Repeater']['Parameters']['ModelAwareness']['MaxAcceptableErrors'] = [MaxAcceptableErrors]
                self.logger.info("Student Repeater: Changing MaxAcceptableErrors to %s" % MaxAcceptableErrors)
                self.execute_experiment(experiment_description)

            experiment_description.update(deepcopy(student_rep_skeleton))
            for RatiosMax in [5, 10, 30]:
                experiment_description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] = [RatiosMax]
                self.logger.info("Student Repeater: Changing RatiosMax to %s" % BaseAcceptableErrors)
                self.execute_experiment(experiment_description)

        return self.counter

    def benchmark_SA(self):

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


def run_benchmark():
    main_api_address = "http://main-node:49152"
    # Container creation performs --volume on `./results/` folder. Change wisely results_storage.
    results_storage = "./results/serialized/"
    try:
        runner = BRISEBenchmark(main_api_address, results_storage)
        try:
            # ---    Add User defined benchmark scenarios execution below  ---#
            # --- Possible variants: benchmark_repeater, benchmark_SA ---#
            runner.benchmark_repeater()

            # --- Helper method to remove outdated experiments from `./results` folder---#
            # runner.move_redundant_experiments(location=runner.results_storage + "outdated/")

            # ---   Add User defined benchmark scenarios execution above   ---#
        except Exception as err:
            logging.warning("The Benchmarking process interrupted by an exception: %s" % err)
            runner.main_api_client.stop_main()
        finally:
            runner.main_api_client.stop_main()
            chown_files_in_dir(results_storage)
            logging.info("The ownership of dump files was changed, exiting.")
    except Exception as err:
        logging.error("Unable to create BRISEBenchmark instance: %s" % err)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The entry point of BRISE Benchmark service.")
    parser.add_argument("mode", choices=["analyse", "benchmark"], help="Mode in which Benchmarking functionality should be runned.")
    args = parser.parse_args()

    if args.mode == "analyse":
        build_benchmark_report()
    else:   # args.mode == "benchmark"
        run_benchmark()
