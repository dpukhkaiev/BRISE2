import numpy as np
import logging


class OutlierDetector:
    def _find_outliers(self, input_data: dict): pass

    def _validate_conditions_for_od(self, input_data: dict, outliers: list, criterions_used: int):
        return outliers, criterions_used

    def outlier_detection(self, tasks, result_structure):
        """
        Finds and marks outliers values for 1 configuration
        :param tasks: list of results for 1 configuration that should be checked
        :param result_structure: specify user-defined structure of results (name, type etc.)
        :return: list of results, list of marks for report, number of used outliers detection criterias
        """
        delete_rows = np.array([])
        input_size = len(tasks)
        criterions_used_number = 0
        for index_i, parameter in enumerate(result_structure):
            outliers = []
            criterions_used = []
            input_data = np.array([])
            input_data_full = np.array([])
            for index_j in range(0,input_size):
                input_data_full = np.append(input_data_full, tasks[index_j]['result'][parameter])
                # filter dataset
                if tasks[index_j]['ResultValidityCheckMark'] != "Bad value" and tasks[index_j]['ResultValidityCheckMark'] != "Out of bounds":
                    # no need to operate with bad values from error check script
                    input_data = np.append(input_data, tasks[index_j]['result'][parameter]) 
            outliers, criterions_used = self._validate_conditions_for_od(input_data, outliers, criterions_used)
            criterions_used_number = criterions_used.count(True)
            # find indexes of outliers in filtered dataset
            for index_i in range(0, len(outliers)):
                if criterions_used[index_i] == True:
                    for index_j in range(0, len(outliers[index_i])):
                        i = np.where(input_data_full == str(outliers[index_i][index_j]))
                        j = np.where(input_data_full == outliers[index_i][index_j])
                        delete_rows = np.append(delete_rows, i)
                        delete_rows = np.append(delete_rows, j)
            # find indexes of outliers in original dataset
            outliers_position = np.array([])
            unique, counts = np.unique(delete_rows, return_counts = True)
            for index in range(0,len(counts)):
                if float(counts[index])/float(criterions_used_number) >= 0.5:
                    outliers_position = np.append(outliers_position,unique[index])  
            unique = np.unique(outliers_position)
            # mark outliers in the results
            for index in range(0, len(tasks)):
                if tasks[index]['ResultValidityCheckMark'] == "Outlier":
                    tasks[index]['ResultValidityCheckMark'] = "OK"
            for index_j in sorted(unique.astype(int), reverse = True):
                tasks[index_j]['ResultValidityCheckMark'] = "Outlier"
        return tasks, criterions_used_number

    def _report_according_to_required_structure(self, config, final_results, criterions_used_number):
        """
        Format the results for logging
        :param config: current configuration entity
        :param final_results: task dict with corresponding marks
        :param criterions_used_number: number of used OD criterias
        """
        bad_value_tasks = []
        outbound_value_tasks = []
        outlier_value_tasks = []
        for task in final_results:
            if task['ResultValidityCheckMark'] == 'Bad value':
                bad_value_tasks.append(task['result'])
            elif task['ResultValidityCheckMark'] == 'Out of bounds':
                outbound_value_tasks.append(task['result'])
            elif task['ResultValidityCheckMark'] == 'Outlier':
                outlier_value_tasks.append(task['result'])

        output_message = f"Configuration {config.parameters} has"

        if len(bad_value_tasks) + len(outbound_value_tasks) + len(outlier_value_tasks) == 0:
            output_message += f" no tasks with bad/outbound resulting values or outliers"

        if len(bad_value_tasks) > 0:
            output_message += f" {len(bad_value_tasks)} task(s) with bad values "

        if len(outbound_value_tasks) > 0:
            output_message += f"; {len(outbound_value_tasks)} task(s) with outbound values"

        if len(outlier_value_tasks) > 0:
            output_message += f"; {len(outlier_value_tasks)} task(s) with outlier values, " \
                              f"{criterions_used_number} outlier detection criteria were used"
        output_message += "."

        logging.getLogger(__name__).info(output_message)

    def find_outliers_for_taskset(self, inputs, result_structure, configurations, tasks_to_send):
        """
        Finds and marks outliers values for each configuration in taskset
        :param inputs: list of results for 1 configuration that should be checked
        :param result_structure: specify user-defined structure of results (name, type etc.)
        :param configurations: configurations class object
        :param tasks_to_send: taskset which should be measured
        :return: list of results with marked outliers
        """
        final_results = []
        for config in configurations:
            configuration_inputs = []
            for parameters, result in zip(tasks_to_send, inputs):
                if config.parameters == parameters:
                    configuration_inputs.append(result)
            new_configuration_size = len(configuration_inputs)
            if new_configuration_size > 0:
                previous_results = list(config.get_tasks().values())
                for index in range(0, len(previous_results)):
                    configuration_inputs.append(previous_results[index])
                intermediate_results, criterions_used_number = self.outlier_detection(configuration_inputs, result_structure)
                for index in range(0, new_configuration_size):
                    final_results.append(intermediate_results[index])
                self._report_according_to_required_structure(config, intermediate_results, criterions_used_number)
        return final_results
