

class StopCondition:

    def __init__(self, experiment):
        self.experiment = experiment
    
    def is_finish(self): 
        return False
    
    def get_experiment(self):
        return self.experiment
