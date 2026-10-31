import json
import logging
import os
import unittest
from unittest.mock import MagicMock, patch

from core_entities.configuration import Configuration
from repeater.repeater_selector import RepeaterOrchestration

logging.disable(logging.CRITICAL)

DESCRIPTION = {
    "RepetitionManager": {
        "MaxFailedTasksPerConfiguration": 1,
        "Instance": {"QuantityBased": {"MaxTasksPerConfiguration": 1, "Type": "quantity_based"}}
    }
}
PARAMETERS = {"x": 1}


class TestFailedTaskHandling(unittest.TestCase):
    """
    A Configuration whose Tasks are all rejected must never be dropped silently:
    it is retried until the failure threshold is reached and then reported back
    as measured. Otherwise a Racing rung waits for a result that can
    never arrive.
    """

    def setUp(self):
        Configuration.set_task_config({"Objectives": {"improvement": {"Name": "improvement"}}})
        with patch("repeater.repeater.MongoDB"):
            from repeater.quantity_based import QuantityBasedType
            repeater_type = QuantityBasedType(DESCRIPTION, "experiment")

        self.orchestrator = RepeaterOrchestration.__new__(RepeaterOrchestration)
        self.orchestrator.logger = logging.getLogger(__name__)
        self.orchestrator.experiment_id = "experiment"
        self.orchestrator.database = MagicMock()
        self.orchestrator.performed_measurements = 0
        self.orchestrator.repeater_parameters = {
            **DESCRIPTION["RepetitionManager"]["Instance"]["QuantityBased"],
            **DESCRIPTION["RepetitionManager"]
        }
        self.orchestrator._objectives = ["improvement"]
        self.orchestrator._objectives_data_types = ["float"]
        self.orchestrator._expected_values_range = [(0, 100)]
        self.orchestrator._type = repeater_type

    def _report_failed_task(self, already_failed_tasks):
        """Feed back one Task the worker could not compute, and return what was published."""
        configuration = Configuration(PARAMETERS, Configuration.Type.PREDICTED, "experiment")
        configuration.status['evaluated'] = True
        configuration.number_of_failed_tasks = already_failed_tasks
        body = json.dumps({
            "configuration": configuration.to_json(),
            "tasks_to_send": [PARAMETERS],
            "tasks_results": [{"task id": 1, "worker": "worker", "result": {"improvement": None}}]
        }).encode()

        with patch.dict(os.environ, {"TEST_MODE": "INTEGRATION"}), \
                patch("repeater.repeater_selector.API"), \
                patch("repeater.repeater_selector.publish") as publish:
            self.orchestrator.measure_configurations(None, None, None, body)
        return [call.kwargs for call in publish.call_args_list]

    def test_failed_task_is_retried(self):
        published = self._report_failed_task(already_failed_tasks=0)[-1]
        self.assertEqual(published["exchange"], "process_tasks_exchange")

        message = json.loads(published["body"])
        self.assertEqual(message["tasks"], [PARAMETERS])
        configuration = Configuration.from_json(message["configuration"])
        self.assertEqual(configuration.number_of_failed_tasks, 1)
        self.assertFalse(configuration.status['measured'])

    def test_configuration_is_reported_back_once_it_keeps_failing(self):
        published = self._report_failed_task(already_failed_tasks=1)
        self.assertEqual(published[-1]["exchange"], "configurations_results_exchange")

        configuration = Configuration.from_json(published[-1]["body"])
        self.assertTrue(configuration.status['measured'])
        self.assertFalse(configuration.status['enabled'])
        self.assertEqual(configuration.results, {})

    def test_bad_configuration_is_counted_through_the_experiment_api(self):
        """The Experiment API dispatches on a JSON-encoded method name."""
        published = self._report_failed_task(already_failed_tasks=1)
        api_calls = [call for call in published
                     if call["exchange"] == "experiment_api_exchange"]
        self.assertEqual([json.loads(call["body"]) for call in api_calls],
                         ["increment_bad_configuration_number"])


if __name__ == "__main__":
    unittest.main()
