import logging

from stop_condition.stop_condition_decorator import StopConditionDecorator
from stop_condition.stop_condition_prior import StopConditionPrior


class StopConditionDecoratorPrior(StopConditionDecorator, StopConditionPrior):
    
    def __init__(self, stop_condition, name):
        super().__init__(stop_condition)
        self.logger = logging.getLogger(name)
    
    def validate_conditions(self):
        flag = self.is_finish()
        if flag == True:
            return flag
        else:
            return self.stop_condition.validate_conditions()
