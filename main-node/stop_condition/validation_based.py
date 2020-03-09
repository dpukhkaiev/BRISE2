from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class ValidationBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.start_threads()

    def is_finish(self):
        last_mode_is_valid = self.experiment.get_model_state()
        if last_mode_is_valid:
            self.decision = True
        self.logger.debug(f"Last model was{'' if last_mode_is_valid else ' not'} valid.")
