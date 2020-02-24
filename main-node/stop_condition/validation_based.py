from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class ValidationBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.start_threads()

    def is_finish(self):
        if self.experiment.get_model_state():
            self.logger.info("Validation-based Stop Condition suggested to stop BRISE. "
                             "Model is valid.")
            self.decision = True
            self.update_expression(self.stop_condition_type, self.decision)
