import logging
import time
import os
import json

from reconfiguration.reconfiguration_executor import ReconfigurationExecutor

from core_entities.experiment import Experiment
from configuration_selection.configuration_selection import ConfigurationSelection

from tools.rabbitmq_common_tools import RabbitMQConnection, publish

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

        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.connection_thread = self._EventServiceConnection(self)
            self.connection_thread.start()

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
    def change_variant(self, variability_point:str, new_feature:list[dict]|dict, parent_nodes:None|list=None):
        """Request to change the given variability point to a new variant"""
        # Select prev_feature by Type or Key in feature model or both?
        parent_keys_list = self._get_variability_point_keys(variability_point, parent_nodes)
        if len(parent_keys_list) == 0:
            raise ValueError("Variability point " + variability_point + " was not found in the feature selection!")
        
        # Update the feature selection
        for parent_keys in parent_keys_list:
            self._update_feature_selection(parent_keys, variability_point, new_feature)
        #print("New feature selection", self._new_experiment_description)

        self._requested_changes[variability_point] = {"description": new_feature, "identifiers": parent_nodes}

        return self
    
    @configure_method
    def change_variables(self, variability_point:str, new_values:dict):
        """Request to change the values of a component with a given variability point"""
        # Select prev_feature by Type or Key in feature model or both?
        parent_keys_list = self._get_variability_point_keys(variability_point, None)
        if len(parent_keys_list) == 0:
            raise ValueError("Variability point " + variability_point + " was not found in the feature selection!")
        
        # Update the feature selection
        for parent_keys in parent_keys_list:
            self._update_feature_selection_values(parent_keys, variability_point, new_values)

        self._requested_changes[variability_point + "_Values"] = {"description": new_values, "identifiers": None}

    def request_change(self, ch, method, properties, body):
        """Determine the requested change from the queue"""
        event = json.loads(body.decode())
        event_type = event["type"]
        event_data = event.get("data", {})

        if not isinstance(event_data, dict):
            raise ValueError("Expected event data to be a dictionary!")

        # Handle event based on type (call correct function)
        if event_type == "variant":
            self.change_variant(event_data["vp"], event_data["new_feature"], event_data.get("parent_nodes", None))
        elif event_type == "variables":
            self.change_variables(event_data["vp"], event_data["new_values"])
        elif event_type == "done":
            self.done()
        else:
            raise ValueError("Unknown event type " + str(event_type))

    def done(self):
        """Signal that all reconfiguration requests are done. Set state to CONFIG_FINISHED"""
        assert self.state == State.CONFIG_UNFINISHED, "No configuration requested"
        self.state = State.CONFIG_FINISHED
        return self

    def reconfigure(self):
        """Performs the reconfiguration"""
        assert self.state == State.CONFIG_FINISHED, "No configuration requested or configuration is unfinished"

        # Perform reconfigure plan/requests
        for vp, changes in self._requested_changes.items():
            self.executor.change(vp, changes["description"], self._new_experiment_description, changes["identifiers"])

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

    def _get_variability_point_keys(self, vp:str, required_parent_nodes:None|list) -> list:
        """Returns a list of lists with parent keys for the variability point. All vps must have the given parent nodes. Otherwise they will be ignored"""
        paths = [k.split(" ") for k in self._flatten_keys(self._new_experiment_description, vp)]
        if required_parent_nodes is None or len(required_parent_nodes) == 0:
            return paths
        
        return [p for p in paths if set(p[-len(required_parent_nodes)-1:-1]) == set(required_parent_nodes)]
    
    def _flatten_keys(self, d:dict, search:str, parent_key=""):
        """Returns a list of strings with the flattend keys that end with the given search term. Single keys are separated by white spaces"""
        keys = []

        for key, value in d.items():
            new_key = parent_key + " " + key if parent_key else key
            if key == search:
                keys.append(new_key)
                return keys

            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, search, parent_key=new_key))
                continue

        return keys

    def _update_feature_selection(self, keys:list, parent_key:str, new_value):
        """Update the `_new_experiment_description`"""
        level = self._new_experiment_description
        keys.remove(parent_key)
        for key in keys:
            level = level[key]
        
        level[parent_key] = new_value

    def _update_feature_selection_values(self, keys:list, parent_key:str, new_values:dict):
        """Update all given values in the `_new_experiment_description` for the given path of keys"""
        level = self._new_experiment_description
        keys.remove(parent_key)
        for key in keys:
            level = level[key]
        
        for key, value in new_values.items():
            level[parent_key][key] = value

    class _EventServiceConnection(RabbitMQConnection):
        """
        This class is responsible for listening to 2 queues.
        1. `reconfiguration_exchange` queue for handleing reconfiguration requests.
        2. `stop_components` for shutting down configuration selection module (in case of BRISE Experiment termination).
        """

        def __init__(self, reconf_module):
            """
            The function for initializing consumer thread
            :param configuration_selection: instance of ConfigurationSelection class
            """
            self.reconf_module: ReconfigurationModule = reconf_module
            self.experiment_id = self.reconf_module.configuration_selection.experiment.unique_id
            super().__init__(reconf_module)

        def bind_and_consume(self):
            self.termination_result = self.channel.queue_declare(queue='', exclusive=True)
            self.termination_queue_name = self.termination_result.method.queue
            self.channel.queue_bind(exchange='experiment_termination_exchange',
                                    queue=self.termination_queue_name,
                                    routing_key=self.experiment_id)

            self.channel.basic_consume(queue="reconfiguration_exchange" + self.experiment_id, auto_ack=True,
                                       on_message_callback=self.reconf_module.request_change)
            self.channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                       on_message_callback=self.stop)