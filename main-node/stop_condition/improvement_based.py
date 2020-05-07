from stop_condition.stop_condition import StopCondition


class ImprovementBasedType(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.max_configs_without_improvement = stop_condition_parameters["Parameters"]["MaxConfigsWithoutImprovement"]
        self.start_threads()

    def is_finish(self):
        measured_configurations = self.database.get_records_by_experiment_id("Measured_configurations", self.experiment_id)
        current_solution = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Current_solution"]
        solution_index = next((index for (index, d) in enumerate(measured_configurations) if d["Parameters"] == current_solution["Parameters"]), 0)
        configs_without_improvement = len(measured_configurations) - solution_index
        if configs_without_improvement >= self.max_configs_without_improvement:
            self.decision = True
        else:
            self.decision = False
        self.logger.debug(f"Solution position - {solution_index}. "
                        f"No improvement was made for last {configs_without_improvement} Configurations. "
                        f"Maximum Configurations without improvement - {self.max_configs_without_improvement}.")
