import logging
import time
import datetime

from tools.time_units_convertor import convert_to_seconds
from stop_condition.stop_condition_decorator_prior import StopConditionDecoratorPrior


class TimeBasedType(StopConditionDecoratorPrior):
    """
        Time based stop condition. 
        Simple timer. Triggering of that timer will stop BRISE computations during next SC validation.
    """
    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition)
        self.interval = convert_to_seconds(stop_condition_parameters["TimeUnit"], stop_condition_parameters["MaxRunTime"])

        self.logger = logging.getLogger(__name__)
        self.initial_timestamp = datetime.datetime.now()
        temp_msg = "Timeout is set. !!!WARNING!!! BRISE will not stop at timeout moment due to workflow."
        self.logger.info(temp_msg)

    def is_finish(self):
        current_timestamp = datetime.datetime.now()
        diff = (current_timestamp-self.initial_timestamp).total_seconds()
        if diff >= self.interval:
            self.logger.info("Timeout reached. Time-based Stop Condition suggested to stop BRISE.")
            return True
        else:
            self.logger.info("Time-based Stop Condition suggested to continue running BRISE.")
            return False

