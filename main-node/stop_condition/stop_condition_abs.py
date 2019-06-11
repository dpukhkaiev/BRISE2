from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, is_minimization_experiment, stop_condition_config):
        self.is_minimization_experiment = is_minimization_experiment
        self.stop_condition_config = stop_condition_config
        self.configs_without_improvement = 0
        self.prediction_is_final = False
        self.max_configs_without_improvement = 0
        self.best_solution_configuration = []

    # Template method
    def __validate_solution_candidate(self, solution_candidate_configuration, current_best_configurations):
        """
        Returns prediction_is_final=True if configs_without_improvement >= "MaxConfigsWithoutImprovement",
                otherwise prediction_is_final=False
        :param solution_candidate_configurations: instance of Configuration class
        :param current_best_configurations: list of instances of Configuration class
        :return: prediction_is_final
        """
        if self.best_solution_configuration == [] or self.best_solution_configuration[0] > current_best_configurations[0]:
            self.best_solution_configuration = current_best_configurations

        if self.configs_without_improvement < self.max_configs_without_improvement:
            self.compare_configurations([solution_candidate_configuration], current_best_configurations)
        
        return self.prediction_is_final

    def validate_solution_candidates(self, solution_candidates_configurations, current_best_configurations):
        """
        Returns prediction_is_final=True if configs_without_improvement >= "MaxConfigsWithoutImprovement",
                otherwise prediction_is_final=False
        :param solution_candidates_configurations: list of instances of Configuration class
        :param current_best_configurations: list of instances of Configuration class

        :return: bool True if predicted solution candidate was final, Flase if not final
        """
        was_final = False
        for configuration in solution_candidates_configurations:
            if self.__validate_solution_candidate(configuration, current_best_configurations):
                was_final = True
        return was_final
        
        

    def compare_configurations(self, solution_candidate_configurations, current_best_configurations):
        # If the measured point is better than previous best value - add this point to data set and rebuild model.
        # Assign self.configs_without_improvement to its configuration value.
        if solution_candidate_configurations[0].is_better_configuration(self.is_minimization_experiment, current_best_configurations[0]):
            self.configs_without_improvement = 0
            self.logger.info("New solution is found! Predicted value %s is better than previous value %s. "
                             "Configs Without Improvement = %s" % (solution_candidate_configurations[0].get_average_result(),
                                                                   self.best_solution_configuration[0].get_average_result(),
                                                                   self.configs_without_improvement))
            self.best_solution_configuration = solution_candidate_configurations

        # If the measured point is worse than previous best value - add this point to data set and rebuild model.
        # Decrease self.configs_without_improvement by 1
        else:
            self.configs_without_improvement += 1
            self.logger.info("Predicted value %s is not better than previous value %s. Configs Without Improvement = %s"
                             % (solution_candidate_configurations[0].get_average_result(),
                                self.best_solution_configuration[0].get_average_result(),
                                self.configs_without_improvement))
            if self.configs_without_improvement >= self.max_configs_without_improvement:
                self.prediction_is_final = self.is_final_prediction(current_best_configurations,
                                                                    solution_candidate_configurations)

    @abstractmethod
    def is_final_prediction(self, current_best_configurations, solution_candidate_configurations): pass
