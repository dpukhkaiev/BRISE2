from stop_condition.stop_condition import StopCondition


class StopConditionDecorator(StopCondition):
    
    def __init__(self, stop_condition):
        super().__init__(stop_condition.get_experiment())
        self.stop_condition = stop_condition
    
    def get_experiment(self):
        return self.stop_condition.get_experiment()


