from stop_condition.stop_condition import StopCondition


class StopConditionPrior(StopCondition):
    def __init__(self, experiment):
        super().__init__(experiment)
