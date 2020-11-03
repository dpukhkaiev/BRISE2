import logging
import os
import pickle
import random
import time
from collections import Counter, OrderedDict
from string import ascii_lowercase
from typing import List

import numpy as np
import pandas as pd
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from jinja2 import Environment, FileSystemLoader
from plotly.offline import plot
from plots.box_statistic import box_statistic
from plots.exp_config import exp_description_highlight
from plots.improvements import improvements
from plots.repeat_vs_avg import repeat_vs_avg
# Plots
from plots.table import table
# Tools
from shared_tools import chown_files_in_dir, get_resource_as_string
from sortedcontainers import SortedDict

# from shared_tools import export_plot


class BRISEBenchmarkAnalyser:
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

    def __init__(self, experiments_folder: str, output_folder: str):
        """
        Args:
            folder_with_dumps (str, optional): Path to Experiment instances. Defaults to "./results/serialized/".
        """
        self.experiments_folder = experiments_folder
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Helper fields
        self.__cache = {
            'csv_data': {}
        }
        self._experiments = []

    def get_experiments(self) -> List[Experiment]:
        return self._experiments

    def set_experiments(self, experiments: List[Experiment]):
        if all([issubclass(Experiment, type(item)) for item in experiments]):
            self._experiments = experiments
        else:
            raise TypeError('Not all provided objects are subtypes of the Experiment.')
        return self

    def analyse_repeater_results(self, experiments: List[Experiment] = None):
        if not experiments:
            if not self.get_experiments():
                self.load_experiments()
            experiments = self.get_experiments()

        # Report structure
        table_rows = SortedDict({
            'Student no MA 1 BAE': {'Experiments': []},
            'Student no MA 5 BAE': {'Experiments': []},
            'Student no MA 10 BAE': {'Experiments': []},
            'Student no MA 25 BAE': {'Experiments': []},
            'Student no MA 50 BAE': {'Experiments': []},
            'Student no MA 1 BAE 50 max': {'Experiments': []},
            'Student no MA 5 BAE 50 max': {'Experiments': []},
            'Student no MA 10 BAE 50 max': {'Experiments': []},
            'Student no MA 25 BAE 50 max': {'Experiments': []},
            'Student no MA 50 BAE 50 max': {'Experiments': []},
            'Student MA 1 BAE': {'Experiments': []},
            'Student MA 5 BAE': {'Experiments': []},
            'Student MA 10 BAE': {'Experiments': []},
            'Student MA 25 BAE': {'Experiments': []},
            'Student MA 50 BAE': {'Experiments': []},
            'Student MA 25 MAE': {'Experiments': []},
            'Student MA 50 MAE': {'Experiments': []},
            'Student MA 75 MAE': {'Experiments': []},
            'Student MA 2 RM': {'Experiments': []},
            'Student MA 3 RM': {'Experiments': []},
            'Student MA 5 RM': {'Experiments': []},
            'Student MA 10 RM': {'Experiments': []},
            'Student MA 25 RM': {'Experiments': []}
        })
        # Group experiments per rows
        for exp in experiments:
            # quantity-based
            if exp.description['Repeater']['Type'] == 'default':
                row_name = f"Default {exp.description['Repeater']['Parameters']['MaxTasksPerConfiguration']}"
                if row_name not in table_rows:
                    table_rows[row_name] = {'Experiments': []}
                table_rows[row_name]['Experiments'].append(exp)
            elif exp.description['Repeater']['Type'] == 'student_deviation':
                # not experiment-aware
                if not exp.description['Repeater']['Parameters']['ModelAwareness']['isEnabled']:
                    # 10 max
                    if exp.description['Repeater']['Parameters']['MaxTasksPerConfiguration'] == 10:
                        if exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [50]:
                            table_rows['Student no MA 50 BAE']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [25]:
                            table_rows['Student no MA 25 BAE']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [10]:
                            table_rows['Student no MA 10 BAE']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [5]:
                            table_rows['Student no MA 5 BAE']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [1]:
                            table_rows['Student no MA 1 BAE']['Experiments'].append(exp)
                        else:
                            raise KeyError(exp.description)
                    # 50 max
                    elif exp.description['Repeater']['Parameters']['MaxTasksPerConfiguration'] == 50:
                        if exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [50]:
                            table_rows['Student no MA 50 BAE 50 max']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [25]:
                            table_rows['Student no MA 25 BAE 50 max']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [10]:
                            table_rows['Student no MA 10 BAE 50 max']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [5]:
                            table_rows['Student no MA 5 BAE 50 max']['Experiments'].append(exp)
                        elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [1]:
                            table_rows['Student no MA 1 BAE 50 max']['Experiments'].append(exp)
                        else:
                            raise KeyError(exp.description)
                # experiment-aware
                elif exp.description['Repeater']['Parameters']['ModelAwareness']['isEnabled']:
                    # ratio-max
                    if exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [25]:
                        table_rows['Student MA 20 RM']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [10]:
                        table_rows['Student MA 7 RM']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [5]:
                        table_rows['Student MA 5 RM']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [3] \
                            and exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [5] \
                            and exp.description['Repeater']['Parameters']['MaxAcceptableErrors'] == [50]:
                        table_rows['Student MA 3 RM']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [2]:
                        table_rows['Student MA 2 RM']['Experiments'].append(exp)
                    # MAE
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['MaxAcceptableErrors'] == [75]:
                        table_rows['Student MA 75 MAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['MaxAcceptableErrors'] == [50] \
                            and exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [3] \
                            and exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [5]:
                        table_rows['Student MA 50 MAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['ModelAwareness']['MaxAcceptableErrors'] == [25]:
                        table_rows['Student MA 25 MAE']['Experiments'].append(exp)
                    # BAE
                    elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [50]:
                        table_rows['Student MA 50 BAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [25]:
                        table_rows['Student MA 25 BAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [10]:
                        table_rows['Student MA 10 BAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [5] \
                            and exp.description['Repeater']['Parameters']['ModelAwareness']['RatiosMax'] == [3] \
                            and exp.description['Repeater']['Parameters']['MaxAcceptableErrors'] == [50]:
                        table_rows['Student MA 5 BAE']['Experiments'].append(exp)
                    elif exp.description['Repeater']['Parameters']['BaseAcceptableErrors'] == [1]:
                        table_rows['Student MA 1 BAE']['Experiments'].append(exp)
                    else:
                        raise KeyError(exp.description)

        baseline_time = -1
        # collect the baseline
        for row_name in table_rows.keys():
            if row_name == "Default 10":
                row_exps = table_rows[row_name]['Experiments']
                configs_in_experiment = self.collect_configurations_from_experiments(row_exps)
                tasks_in_experiment = self.collect_tasks_from_configurations(configs_in_experiment)
                summary_results = self.summarize_results_in_tasks(tasks_in_experiment)
                baseline_time = np.round(summary_results.get("time", 0), 4)
        # create csv report
        for row_name in table_rows.keys():
            row_exps = table_rows[row_name]['Experiments']
            configs_in_experiment = self.collect_configurations_from_experiments(row_exps)
            tasks_in_experiment = self.collect_tasks_from_configurations(configs_in_experiment)
            summary_results = self.summarize_results_in_tasks(tasks_in_experiment)

            all_energy_qualities = [self.get_energy_exp_solution_quality(exp, goal_column='EN') for exp in row_exps]
            columns = OrderedDict({
                'Strategy': row_name,
                'Configurations measured': len(configs_in_experiment),
                'Tasks measured': len(tasks_in_experiment),
                'Energy Effort [MJ]': np.round(summary_results.get("energy", 0) / 1000000., 4),
                'Relative Solution Quality': np.round(np.average(all_energy_qualities, axis=0), 4),
                'Time Effort [days]': np.round(summary_results.get("time", 0) / (1000 * 60 * 60 * 24), 4),
                'Relative Time Effort': np.round(summary_results.get("time", 0), 4) / baseline_time
            })

            table_rows[row_name] = columns

        #   Writing results to file
        pd_df = pd.DataFrame(data=table_rows.values())
        pd_df.to_csv("{}{}".format(self.output_folder, "RepeaterBenchmarkAnalysis.csv"), index=False)
        return table_rows

    # ---   Helper methods for Energy experiments ---

    def get_energy_exp_solution_quality(self, experiment: Experiment, goal_column: str = 'EN') -> float:
        """
            The method is designed to derive the relative quality of solution obtained in Energy Experiment.

        :param experiment: energy Experiment instance. Experiment Description should contain ws_file(csv file) name.
        :param goal_column: Str either 'EN' or 'TIM', reflects Energy and Time goals respectively.
        :return: float. Quality of solution suggested by model, compared to the best one, available in the Scenario file.
        """
        file_name = experiment.description["TaskConfiguration"]["Scenario"]["ws_file"]
        csv_data = self.__cache["csv_data"].get(file_name)

        if csv_data is None:
            csv_data = pd.read_csv('./scenarios/energy_consumption/search_space_96/' + file_name).groupby(["FR", "TR"]).mean()
            self.__cache["csv_data"][file_name] = csv_data

        optimum_energy, _ = csv_data.min()[goal_column], csv_data.idxmin()[goal_column]

        found_configuration = experiment.get_current_solution().parameters
        found_energy = csv_data.loc[tuple(found_configuration), goal_column]
        return optimum_energy / found_energy

    # ---   Generic helper methods, that could be used in any benchmark analysis ---
    def load_experiments(self):
        """ De-serializing a Python object structure from binary files in provided folder.

        Returns:
            Experiments_Analyser object with loaded experiments.
        """
        logger = logging.getLogger(__name__)

        # ------- List with name experiment instances. Default from ./results/serialized/ folder
        experiment_dumps = [f for f in os.listdir(self.experiments_folder) if (f[-4:] == '.pkl')]
        # -------
        if experiment_dumps:
            logger.info("Selected %s Experiment dumps for report." % len(experiment_dumps))
        else:
            raise FileNotFoundError("Directory '%s' is empty." % self.experiments_folder)

        exp = []
        for index, file_name in enumerate(experiment_dumps):
            with open(self.experiments_folder + file_name, 'rb') as input_:
                instance = pickle.load(input_)
                instance.color = BRISEBenchmarkAnalyser.COLORS[index % len(BRISEBenchmarkAnalyser.COLORS)]
                exp.append(instance)

        self.set_experiments(exp)
        return self

    def reduce_duplicated_experiments_by_id(self, strategy: str = 'avg'):
        """
        Method takes a list of Experiments, finds an Experiments that were repeated (based on an ID field of en Experiment),
        and reduces the repetitions according to desired strategy.

        :param strategy: string. The default value - 'avg'.
                The way how the same experiments are combined. Possible strategies:
                - 'avg' - pick the one with the average solution Configuration result
                    for instance, you have 3 Experiment, the solution Configurations are respectively
                    [315.223], [524.944], [788.444], the 'avg' strategy will pick the Experiment with [524.944] solution .
                - 'min' - pick the Experiment with the lowest result Configuration.
                - 'max' - pick the Experiment with the biggest result Configuration.
                - 'merge' - Strategy to merge a bunch of same Experiments, should discuss in future, not implemented yet.

        :return: list of unique Experiments.
        """

        # Group repeated experiment by id field in groups.
        groups = []
        ids = [exp.ed_id for exp in self.get_experiments()]
        indices_for_sorting = np.argsort(ids)

        group_of_same_experiments = []
        for index in indices_for_sorting:
            if len(group_of_same_experiments) == 0 or \
                    self.get_experiments()[index].ed_id == group_of_same_experiments[-1].ed_id:
                group_of_same_experiments.append(self.get_experiments()[index])
            else:
                groups.append(group_of_same_experiments)
                group_of_same_experiments = []

        # Leave one Experiment over all others.
        # For each group, according to the strategy
        for index, group_of_same_experiments in enumerate(groups):
            results_in_experiments = [exp.get_current_solution().get_average_result() for exp in
                                      group_of_same_experiments]

            if strategy == 'max':
                index_of_chosen_experiment = results_in_experiments.index(max(results_in_experiments))
            elif strategy == 'min':
                index_of_chosen_experiment = results_in_experiments.index(min(results_in_experiments))
            elif strategy == 'avg':
                avg_result = np.mean(results_in_experiments)
                index_of_chosen_experiment = results_in_experiments.index(
                    min(results_in_experiments, key=lambda x: abs(x - avg_result)))
            else:
                raise KeyError("The strategy '%s' is not supported." % strategy)

            # Replace a group of experiments with chosen experiment
            chosen_experiment = group_of_same_experiments[index_of_chosen_experiment]
            groups[index] = chosen_experiment

        self.set_experiments(groups)
        return self

    @staticmethod
    def compare_solution_to_default(experiment: Experiment) -> dict:
        default_configuration_tasks = experiment.search_space.get_default_configuration().get_tasks()
        solution_configuration_tasks = experiment.get_current_solution().get_tasks()

        default_results = BRISEBenchmarkAnalyser.summarize_results_in_tasks(default_configuration_tasks)
        solution_results = BRISEBenchmarkAnalyser.summarize_results_in_tasks(solution_configuration_tasks)

        comparison = {}
        for goal in default_results.keys():
            comparison[goal] = default_results[goal] / solution_results[goal]

        return comparison

    @staticmethod
    def collect_tasks_from_configurations(configs: List[Configuration]) -> List[dict]:
        return [task for config in configs for task in config.get_tasks().values()]

    @staticmethod
    def collect_configurations_from_experiments(experiments: List[Experiment]) -> List[Configuration]:
        results = []
        for exp in experiments:
            results.extend(exp.measured_configurations)
        return results

    @staticmethod
    def collect_solutions_from_experiments(experiments: List[Experiment]) -> List[Configuration]:
        return [exp.get_current_solution() for exp in experiments]

    @staticmethod
    def compute_avg_results_over_configurations(configurations: List[Configuration]) -> List[float]:

        # Make sure, that all Configurations are the same points in a search space:
        assert all([config.parameters == configurations[0].parameters for config in configurations])
        tasks = BRISEBenchmarkAnalyser.collect_tasks_from_configurations(configurations)

        previous_task_configuration = Configuration.TaskConfiguration
        Configuration.set_task_config(configurations[0].TaskConfiguration)

        tmp_configuration = Configuration(configurations[0].parameters, Configuration.Type.TEST)
        tmp_configuration.add_tasks(task=tasks)

        result = tmp_configuration.get_average_result()
        Configuration.set_task_config(previous_task_configuration)

        return result

    @staticmethod
    def summarize_results_in_tasks(tasks: List[dict]) -> dict:
        result = Counter()
        for task in tasks:
            result.update(task['result'])
        return dict(result)

    # ---   Report generation templates ---
    def build_detailed_report(self):
        """ Generate report files from the Experiment class instances.
        """

        # --- Generate template
        file_loader = FileSystemLoader("./templates")
        env = Environment(loader=file_loader)
        env.globals['get_resource_as_string'] = get_resource_as_string
        template = env.get_template('index.html')

        # --- Restore experiments for benchmarking

        exp_list = self.load_experiments().reduce_duplicated_experiments_by_id().get_experiments()

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
        with open("{}report_{}.html".format(self.output_folder, suffix), "w", encoding='utf-8') as outf:
            outf.write(html)

        # # Export plots
        # for plt in [table(exp_list), improvements(exp_list), box_statistic(exp_list)]:
        #     export_plot(plot=plt, wight=1200, height=600)

        # Using a host machine User ID to change the owner for the files(initially, the owner was a root).
        chown_files_in_dir(self.output_folder)
