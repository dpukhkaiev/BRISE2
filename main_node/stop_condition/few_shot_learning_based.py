import os
from stop_condition.stop_condition import StopCondition
from core_entities.configuration import Configuration


class FewShotLearningBased(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.start_threads()

    def is_finish(self):
        measured_configurations = self.database.get_records_by_experiment_id("Configuration", self.experiment_id)
        for configuration in measured_configurations:
            if configuration["Type"] == Configuration.Type.TRANSFERRED:
                self.logger.debug("Configuration with type TRANSFERRED was measured: {configuration}")
                self.decision = True
