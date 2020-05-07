import datetime

from stop_condition.stop_condition import StopCondition


class TimeBased(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.interval = datetime.timedelta(**{
                stop_condition_parameters["Parameters"]["TimeUnit"]: stop_condition_parameters["Parameters"]["MaxRunTime"]
            }).total_seconds()
        temp_msg = f"Timeout set to {self.interval} seconds."
        self.logger.info(temp_msg)
        self.time_started = datetime.datetime.now()
        self.start_threads()

    def is_finish(self):
        seconds_elapsed = (datetime.datetime.now() - self.time_started).total_seconds()
        if seconds_elapsed > self.interval:
            self.decision = True
        self.logger.debug(f"{seconds_elapsed} out of {self.interval} seconds elapsed.")
