from stop_condition.stop_condition_decorator_posterior import StopConditionDecoratorPosterior


class ImprovementBasedType(StopConditionDecoratorPosterior):

    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition, __name__)
        self.max_configs_without_improvement = stop_condition_parameters["MaxConfigsWithoutImprovement"]
        self.number_of_configurations_in_iteration = 1
        self.configurations_without_improvement = 0

    def is_finish(self):
        if self.get_configurations_without_improvement() >= self.max_configs_without_improvement:
            self.logger.info("Improvement-Based Stop Condition suggested to stop BRISE.")
            return True
        else:
            self.logger.info("Improvement-Based Stop Condition suggested to continue running BRISE.")
            return False

    def _compare_best_configurations(self, candidate_configurations):
        if(super()._compare_best_configurations(candidate_configurations)):
            self.set_configurations_without_improvement(0)
        else:
            self.set_configurations_without_improvement(self.get_configurations_without_improvement() + self.number_of_configurations_in_iteration)
            self.logger.info("Evaluated Configuration(s) without improvement: %s"
                             % (self.get_configurations_without_improvement()))

    def set_configurations_without_improvement(self, value):
        self.configurations_without_improvement = value

    def get_configurations_without_improvement(self):
        return self.configurations_without_improvement
    
    def validate_conditions(self):
        self._compare_best_configurations(self.get_experiment().get_current_best_configurations())
        return super().validate_conditions()

