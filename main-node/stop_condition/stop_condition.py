import logging

class StopCondition:
    """
        Basic Stop Condition checks number of measured Configurations and if it >= ["NumberOfInitialConfigurations"] + 1 (1 - Default configuration)
        suggest to stop BRISE.
        Also, compare Configurations to save it as a `best_configurations` in an iteration.
        Basic Stop Condition is a core for all Stop Conditions. Each new Stop Condition is a wrapper for the previous one.
    """
    def __init__(self, experiment):
        self.experiment = experiment
        self.best_configurations = experiment.get_current_best_configurations()
        self.logger = logging.getLogger(__name__)
        
        self.max_configs = experiment.get_selection_algorithm_parameters()["NumberOfInitialConfigurations"] + 1

    def validate_conditions(self):
        """
        This method contains two method calls and represents the main functionality of Stop Condition
        :return: bool result of `self.is_finish()` method
        """
        self._update_best_configurations(self.experiment.get_current_best_configurations())

        return self.is_finish()

    def _update_best_configurations(self, candidate_configurations):
        """
        If the new Configuration is better then `self.best_configurations`, it will be updated to the `candidate_configurations`.
        :param candidates_configurations: list of instances of Configuration class
        """
        if self._compare_best_configurations(candidate_configurations):
            self.logger.info("Currently best found Configuration was updated %s -> %s" % (self.best_configurations[0], candidate_configurations[0]))
            self.best_configurations = candidate_configurations
        else:
            self.logger.info("None of measured Configurations are better than currently best found Configuration %s."
                             % (self.best_configurations[0]))

    def _compare_best_configurations(self, candidate_configurations):
        """
        Compare current best Configuration from the Experiment with current best Configuration currently stored in the Stop Condition.
        :param candidate_configurations: list of instances of Configuration class
        :return: bool True if current best configuration is better than previous, otherwise False
        """
        return candidate_configurations[0].is_better_configuration(self.get_experiment().is_minimization(), self.best_configurations[0])

    def update_number_of_configurations_in_iteration(self, number_of_configurations_in_iteration): pass

    def is_finish(self):
        number_of_measured_configurations = self.experiment.get_number_of_measured_configurations()
        if number_of_measured_configurations == self.experiment.get_search_space_size():
            self.logger.info("BRISE has measured the entire Search Space. Reporting the best found Configuration.")
            return True
        elif number_of_measured_configurations >= self.max_configs:
            self.logger.info("Basic Stop Condition suggested to stop BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return True
        else:
            self.logger.info("Basic Stop Condition suggested to continue running BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return False
    
    def get_experiment(self):
        return self.experiment
    
    def get_best_configurations(self):
        return self.best_configurations
