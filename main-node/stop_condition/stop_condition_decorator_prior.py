from stop_condition.stop_condition_decorator import StopConditionDecorator
from stop_condition.stop_condition_prior import StopConditionPrior


class StopConditionDecoratorPrior(StopConditionDecorator, StopConditionPrior):
    
    def __init__(self, stop_condition):
        super().__init__(stop_condition)
