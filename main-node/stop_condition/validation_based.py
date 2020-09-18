from stop_condition.stop_condition import StopCondition


class ValidationBasedType(StopCondition):
    # TODO: this stop condition should be revised,
    #  since there is no clear notion "valid model was build" in three-shaped search space

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.start_threads()
    def is_finish(self):
        last_model_is_valid = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["is_model_valid"]
        if last_model_is_valid:
            self.decision = True
        self.logger.debug(f"Last model was{'' if last_model_is_valid else ' not'} valid.")
