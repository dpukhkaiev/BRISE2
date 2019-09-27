

class StopCondition:
    """
        Basic Stop Condition checks number of measured Configurations and if it >= ["NumberOfInitialConfigurations"] + 1 (1 - Default configuration)
        suggest to stop BRISE.
        Also, compare Configurations to save it as a `best_configurations` in an iteration.
        Basic Stop Condition is a core for all Stop Conditions. Each new Stop Condition is a wrapper for the previous one.
    """
    def __init__(self, experiment):
        self.experiment = experiment
    
    def is_finish(self): 
        return False
    
    def get_experiment(self):
        return self.experiment
