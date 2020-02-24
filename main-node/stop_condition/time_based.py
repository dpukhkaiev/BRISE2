import time
import datetime

from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class TimeBased(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.interval = datetime.timedelta(**{
                stop_condition_parameters["Parameters"]["TimeUnit"]: stop_condition_parameters["Parameters"]["MaxRunTime"]
            }).total_seconds()
        self.start_threads()

    def self_evaluation(self):
        temp_msg = f"Timeout set to {self.interval} seconds."
        self.logger.info(temp_msg)

        self.counter = 0
        while self.thread_is_active:
            time.sleep(1)
            self.counter = self.counter + 1
            if self.counter >= self.interval:
                self.logger.info("Timeout reached.")
                self.decision = True
                self.update_expression(self.stop_condition_type, self.decision)
    
    def is_finish(self): pass
