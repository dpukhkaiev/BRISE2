from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class ImprovementBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.max_configs_without_improvement = stop_condition_parameters["Parameters"]["MaxConfigsWithoutImprovement"]
        self.start_threads()

    def is_finish(self):
        solution_index = self.experiment.measured_configurations.index(self.experiment.get_current_solution())
        configs_without_improvement = len(self.experiment.measured_configurations) - solution_index
        if configs_without_improvement >= self.max_configs_without_improvement:
            self.decision = True
        else:
            self.decision = False
        self.logger.debug(f"Solution position - {solution_index}. "
                          f"No improvement was made for last {configs_without_improvement} Configurations. "
                          f"Maximum Configurations without improvement - {self.max_configs_without_improvement}.")
