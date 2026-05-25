import datetime
import time

from reconfiguration.reconfiguration_module import ReconfigurationModule
from stop_condition.stop_condition_selector import StopConditionSelector
from stop_condition.time_based import TimeBased

class ReconfigurationBehaviourMock:
    """This class handles the reconfiguration requests that are speficied/mocked in the experiment description
    
    Reconfiguration behaviour can be specified under the key `Reconfiguration`.
    Direct child keys are the so called "triggers" i.e. the conditions for the reconfiguration to occur.
    Triggers can have more keys to specify the condition further.
    There must also be a `vp` (variability point) or `variables` and `description` of the changed variability point needs to be specified.
    Duplicate trigger types and be marked with a suffic `_NUM` to differntiate between them.

    Possible parameters for every action:
    - performAmount (int): How often the action will be performed
    """

    def __init__(self, reconf_module:ReconfigurationModule):
        self.reconf_module = reconf_module
        self._experiment = reconf_module.experiment
        self._cs = reconf_module.configuration_selection

        self._reconfigurations = None
        if "Reconfiguration" in self.reconf_module.experiment.description:
            self._reconfigurations = self.reconf_module.experiment.description["Reconfiguration"]

        # Holds all action functions/triggers for the reconfigurations
        self._reconf_actions = {
            "AfterDefault": self._after_default_conf_trigger,
            "NewConfiguration": lambda: True, # Perform every time/on every new conf
            "AfterXConfigurations": self._after_x_confs_trigger,
            "TimeLeft": self._time_left_trigger,
        }

        # Data for triggers
        self.__configuration_count = 0
        self.__performed_actions = []

    def new_configuration_measured(self, configuration):
        """Called by main loop after a new configuration has been evaluated. Check for any specified reconfigurations"""
        # No reconfigurations specified
        if self._reconfigurations is None:
            return
        
        self.__configuration_count += 1
        
        # Check all specified triggers/actions
        for trigger, action in self._reconfigurations.items():            
            # Check how often the action was performed/if it should be performed
            performAmount = action.get("performAmount")
            if performAmount is not None:
                if len([a for a in self.__performed_actions if a == action]) >= performAmount:
                    continue

            if self._reconf_actions[trigger.split("_")[0]](action) is True:
                self.__perform_action(action)
                #print("Performed action:", action)
                #time.sleep(2)

        # Finish the reconfiguration process if any change was requested
        if self.reconf_module.unfinished_configuration():
            self.reconf_module.done()

    def _after_default_conf_trigger(self, action):
        """Perform the action after the default configuration was measured"""
        return len(self._experiment.measured_configurations) < 3 #TODO: Get values that is adapted to all experiemnts

    def _after_x_confs_trigger(self, action):
        """Perform action after `amount` of new configurations"""
        return self.__configuration_count % action["amount"] == 0

    def _time_left_trigger(self, action):
        """Perform the action if a TimeBased SC exists and the time is less than specified in `time`"""
        if action in self.__performed_actions: # Force "once" behaviour
            return False
        
        time_trashold = action["time"]
        for sc in [c for c in StopConditionSelector.stop_conditions if isinstance(c, TimeBased)]:
            seconds_elapsed = (datetime.datetime.now() - sc.time_started).total_seconds()
            if sc.interval - seconds_elapsed <= time_trashold:
                return True

    def __perform_action(self, action):
        """Perform the given action"""
        # Test for keys or the the program fail to show the missing key?

        desc = action["description"]
        identifiers = action.get("identifiers")

        if "vp" in action:
            self.reconf_module.change_variant(action["vp"], desc, identifiers)
        elif "variables" in action:
            self.reconf_module.change_variables(action["variables", desc, identifiers])
        else:
            print("Action can not be performed neither \"vp\" nor \"variables\" key was specified! Action:", action)

        self.__performed_actions.append(action)
