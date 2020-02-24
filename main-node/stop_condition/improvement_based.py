from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class ImprovementBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.max_configs_without_improvement = stop_condition_parameters["Parameters"]["MaxConfigsWithoutImprovement"]
        self.start_threads()

    def is_finish(self):

        solution_index = self.experiment.measured_configurations.index(self.experiment.get_current_solution())
        if (len(self.experiment.measured_configurations) - solution_index) >= self.max_configs_without_improvement:
            self.logger.info("Improvement-based Stop Condition suggested to stop BRISE. "
                             "Solution position - %s. "
                             "Configurations without improvement - %s" %(solution_index, len(self.experiment.measured_configurations) - solution_index))
            self.decision = True
        else:
            self.logger.info("Improvement-based Stop Condition suggested to continue BRISE. "
                             "Solution position - %s. "
                             "Configurations without improvement - %s" %(solution_index, len(self.experiment.measured_configurations) - solution_index))
            self.decision = False
        self.update_expression(self.stop_condition_type, self.decision)
