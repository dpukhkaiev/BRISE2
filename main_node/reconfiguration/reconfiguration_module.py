import logging
import time

from reconfiguration.reconfiguration_executor import ReconfigurationExecutor

from core_entities.experiment import Experiment
from configuration_selection.configuration_selection import ConfigurationSelection

from enum import Enum
from copy import deepcopy

# Determines how long to wait for unfinished configurations before skipping them for the next round of iteration
RECONFIGURATION_TIMEOUT = 10 # time in seconds

class State(Enum):
    IDLE = 0 # No configuration requested or ongoing
    CONFIG_UNFINISHED = 1 # Reconfiguration requested but not all data received (waiting for .reconfigure())
    CONFIG_FINISHED = 2 # All reconfiguration data received

class ReconfigurationModule():
    """Handle reconfiguration of all components"""

    def __init__(self, experiment:Experiment, configuration_selection:ConfigurationSelection):
        self.state = State.IDLE
        self.logger = logging.getLogger(__name__)

        self.experiment = experiment
        self.configuration_selection = configuration_selection

        # Current feature selection
        self._new_experiment_description = deepcopy(experiment.description)

        # Stores requested changes that will be performed by the executor
        self._requested_changes = {}

        self.executor = ReconfigurationExecutor()

    ### Annotations ###
    def configure_method(func):
        """Assert that configuring is allowed. Sets the state to CONFIG_UNFINISHED"""
        def inner(self, *args, **kwargs):
            assert self.state == State.IDLE or self.state == State.CONFIG_UNFINISHED,\
                "Configuring not allowed in state " + self.state.name
            
            self.state = State.CONFIG_UNFINISHED
            result = func(self, *args, **kwargs)
            
            return result
        return inner

    @configure_method
    def change_variant(self, variability_point:str, new_feature:list[dict]|dict):
        """Request to change the given variability point to a new feature"""
        # Select prev_feature by Type or Key in feature model or both?
        parent_keys = self._get_variability_point(variability_point, self._new_experiment_description, [])
        if parent_keys is None:
            raise ValueError("Variability point " + variability_point + " was not found in the feature selection!")

        # Update the feature selection
        self._update_feature_selection(parent_keys, variability_point, new_feature)
        #print("New feature selection", self._new_experiment_description)

        self._requested_changes[variability_point] = new_feature

        return self

    def done(self):
        """Signal that all reconfiguration requests are done. Set state to CONFIG_FINISHED"""
        assert self.state == State.CONFIG_UNFINISHED, "No configuration requested"
        self.state = State.CONFIG_FINISHED
        return self

    def reconfigure(self):
        """Performs the reconfiguration"""
        assert self.state == State.CONFIG_FINISHED, "No configuration requested or configuration is unfinished"

        # Perform reconfigure plan/requests
        for vp, new_feature in self._requested_changes.items():
            self.executor.change(vp, new_feature, self._new_experiment_description)

        # Update experiment description (so the stop condition and repeatition management can use the description??)
        # Make it not read only??
        #self.experiment.description = self._new_experiment_description

        self.state = State.IDLE

    def check_for_reconfiguration(self) -> bool:
        """Check if a new configuration was provided. Wait for unfinished configurations to be finished.
        
        Return True if the configuration was performed (for unit tests)"""
        if self.unfinished_configuration():
            self.logger.info("Waiting for reconfiguration to finish...")

        # Waiting timeout
        start_time = time.time()
        while self.unfinished_configuration() and (time.time() - start_time < RECONFIGURATION_TIMEOUT):
            time.sleep(0.5)
            pass
        
        # Skip message
        if self.unfinished_configuration():
            self.logger.info("Skipped unfinished configuration requests. Attempt to reconfigure next time.")
            return False

        # Perform reconfiguration
        if self.finished_configuration():
            self.logger.info("Performing reconfiguration...")
            self.reconfigure()

            return True
        
        return False

    def unfinished_configuration(self):
        """Return True if the state is CONFIG_UNFINSIHED. Need to wait for more configuration input"""
        return self.state == State.CONFIG_UNFINISHED
    
    def finished_configuration(self):
        """Return True if the state is CONFIG_FINISHED. Can call reconfigure()"""
        return self.state == State.CONFIG_FINISHED

    def _get_variability_point(self, vp:str, feature_selection:dict, parents_keys:list) -> list:
        """Returns a list of parent keys for the variability point"""
        if vp in feature_selection:
            parents_keys.insert(0, vp)
            return parents_keys
        
        for key, value in feature_selection.items():
            if isinstance(value, dict):
                result = self._get_variability_point(vp, value, parents_keys)
                if result is not None:
                    result.insert(0, key)
                    return result
        
        return None

    def _update_feature_selection(self, keys:list, parent_key:str, new_value):
        """Update the `_new_experiment_description`"""
        level = self._new_experiment_description
        keys.remove(parent_key)
        for key in keys:
            level = level[key]
        
        level[parent_key] = new_value