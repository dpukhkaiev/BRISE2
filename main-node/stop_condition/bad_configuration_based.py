from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class BadConfigurationBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.threshold = stop_condition_parameters["Parameters"]["MaxBadConfigurations"]
        self.start_threads()

    def is_finish(self):
        bad_configurations_number = self.experiment.get_bad_configuration_number()
        if bad_configurations_number >= self.threshold:
            self.decision = True
        self.logger.debug(f"Currently {bad_configurations_number} bad Configurations in Experiment.")
