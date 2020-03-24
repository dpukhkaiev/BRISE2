from selection.selection_algorithm_abs import SelectionAlgorithm
from core_entities.experiment import Experiment


class ConfigSpaceSelector(SelectionAlgorithm):
    def __init__(self, experiment: Experiment):
        """
        Creates ConfigSpaceSelector instance that stores information about number of generated points
        :param experiment: the instance of Experiment class
        """
        super().__init__(experiment)
        self.search_space = experiment.search_space

    def get_next_configuration(self):    
        """
            Will return next data point imposed to the search space 
            (`Mersenne Twister pseudo-random generator is used as a core <https://docs.python.org/3/library/random.html>`_).
        :return: list - point in current search space.
        """  

        candidate = self.search_space.sample_configuration()
        try:
            self.logger.debug("Retrieving new configuration from ConfigSpace: %s" % str(candidate))
            return candidate
        except Exception:
            self.logger.error("Selector was not able to get new configuration!")
