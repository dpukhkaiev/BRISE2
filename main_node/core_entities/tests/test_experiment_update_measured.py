import logging
import unittest
from unittest.mock import MagicMock, patch

from core_entities.configuration import Configuration

logging.disable(logging.CRITICAL)

DESCRIPTION = {
    "Context": {"TaskConfiguration": {
        "TaskName": "test",
        "Objectives": {"Y1": {"Name": "Y1", "Minimization": True}}
    }}
}


def make_configuration(parameters, objective_value, task_count):
    Configuration.set_task_config(DESCRIPTION["Context"]["TaskConfiguration"])
    configuration = Configuration(parameters, Configuration.Type.PREDICTED, "experiment")
    configuration._tasks = {str(i): {} for i in range(task_count)}
    configuration.results = {"Y1": objective_value}
    return configuration


class TestExperimentUpdateMeasured(unittest.TestCase):
    """The Racing write-back: a promoted survivor replaces its rung-0 record."""

    def setUp(self):
        with patch("core_entities.experiment.MongoDB"), patch("core_entities.experiment.API"):
            from core_entities.experiment import Experiment
            self.experiment = Experiment(DESCRIPTION, search_space=MagicMock())

    def test_higher_budget_replaces_stored_record(self):
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        self.experiment.measured_configurations = [rung0]
        self.experiment.current_best_configurations = [rung0]

        promoted = make_configuration({"x": 1}, objective_value=0.4, task_count=9)
        self.assertTrue(self.experiment.update_measured_configuration(promoted))
        self.assertEqual(len(self.experiment.measured_configurations), 1)
        self.assertEqual(len(self.experiment.measured_configurations[0].get_tasks()), 9)
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.4)

    def test_no_update_when_not_more_tasks(self):
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=3)
        self.experiment.measured_configurations = [rung0]
        self.experiment.current_best_configurations = [rung0]

        same_budget = make_configuration({"x": 1}, objective_value=0.1, task_count=3)
        self.assertFalse(self.experiment.update_measured_configuration(same_budget))
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.5)

    def test_failed_re_measurement_keeps_the_stored_record(self):
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        self.experiment.measured_configurations = [rung0]
        self.experiment.current_best_configurations = [rung0]

        failed = make_configuration({"x": 1}, objective_value=0.4, task_count=0)
        failed.task_budget = 9
        failed.results = {}
        failed.status["enabled"] = False
        self.assertFalse(self.experiment.update_measured_configuration(failed))
        self.assertIs(self.experiment.measured_configurations[0], rung0)

    def test_no_update_for_unknown_parameters(self):
        self.experiment.measured_configurations = [make_configuration({"x": 1}, 0.5, 1)]
        unknown = make_configuration({"x": 2}, 0.1, 9)
        self.assertFalse(self.experiment.update_measured_configuration(unknown))

    def test_task_time_promotion_replaces_record_with_one_task(self):
        """
        A task_time rung raises the budget of a single Task, so the survivor comes
        back with the same Task count and a higher task_budget. Counting Tasks
        alone would reject it.
        """
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        rung0.task_budget = 1
        self.experiment.measured_configurations = [rung0]
        self.experiment.current_best_configurations = [rung0]

        promoted = make_configuration({"x": 1}, objective_value=0.4, task_count=1)
        promoted.task_budget = 3
        self.assertTrue(self.experiment.update_measured_configuration(promoted))
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.4)

        same_rung_again = make_configuration({"x": 1}, objective_value=0.1, task_count=1)
        same_rung_again.task_budget = 3
        self.assertFalse(self.experiment.update_measured_configuration(same_rung_again))
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.4)

    def test_promotion_can_change_the_best(self):
        winner = make_configuration({"x": 1}, objective_value=0.9, task_count=1)  # looks worst at rung 0
        other = make_configuration({"x": 2}, objective_value=0.6, task_count=1)
        self.experiment.measured_configurations = [winner, other]
        self.experiment.current_best_configurations = [other]

        # higher-budget re-measurement reveals it is actually the best
        promoted = make_configuration({"x": 1}, objective_value=0.3, task_count=9)
        self.assertTrue(self.experiment.update_measured_configuration(promoted))
        self.assertEqual(self.experiment.get_current_solution().parameters, {"x": 1})
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.3)


class TestExperimentUpdateSideEffects(unittest.TestCase):
    """
    A promotion re-measures a Configuration that is already in the Experiment, so
    it must correct what is stored rather than add to it.
    """

    def setUp(self):
        with patch("core_entities.experiment.MongoDB"), patch("core_entities.experiment.API"):
            from core_entities.experiment import Experiment
            self.experiment = Experiment(DESCRIPTION, search_space=MagicMock())
        self.experiment.database = MagicMock()

    def _seed(self, *configurations):
        self.experiment.measured_configurations = list(configurations)
        self.experiment.current_best_configurations = [configurations[0]]
        # one curve entry per measured Configuration, as the add path produces
        self.experiment.current_best_curve = [c.results for c in configurations]

    def test_stored_record_is_updated_not_duplicated(self):
        """
        A second Configuration row for the same measurement would inflate every
        consumer that counts the collection - ImprovementBasedSC derives
        "Configurations without improvement" from a position in exactly that list.
        """
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        self._seed(rung0)

        promoted = make_configuration({"x": 1}, objective_value=0.4, task_count=9)
        promoted.unique_id = rung0.unique_id
        self.assertTrue(self.experiment.update_measured_configuration(promoted))

        self.experiment.database.write_one_record.assert_not_called()
        configuration_updates = [c for c in self.experiment.database.update_record.call_args_list
                                 if c.kwargs.get("collection_name") == "Configuration"]
        self.assertEqual(len(configuration_updates), 1)
        query = configuration_updates[0].kwargs["query"]
        self.assertEqual(query["Configuration_ID"], rung0.unique_id)
        self.assertEqual(query["Exp_unique_ID"], promoted.experiment_id)
        self.assertEqual(configuration_updates[0].kwargs["new_val"]["Results"], {"Y1": 0.4})

    def test_curve_keeps_one_entry_per_measured_configuration(self):
        """
        current_best_curve is consumed positionally against the per-Configuration
        prediction_infos (transfer_learning dynamic_model_recommendation), so an
        extra entry per promotion would shift the curve against its samples.
        """
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        other = make_configuration({"x": 2}, objective_value=0.6, task_count=1)
        self._seed(rung0, other)
        self.assertEqual(len(self.experiment.current_best_curve), 2)

        promoted = make_configuration({"x": 1}, objective_value=0.4, task_count=9)
        self.assertTrue(self.experiment.update_measured_configuration(promoted))
        self.assertEqual(len(self.experiment.current_best_curve), 2)
        self.assertEqual(len(self.experiment.measured_configurations), 2)

    def test_best_may_regress_when_the_cheap_reading_was_optimistic(self):
        """
        The higher-fidelity reading is the one to trust, even when it is worse.
        """
        optimistic = make_configuration({"x": 1}, objective_value=0.2, task_count=1)
        other = make_configuration({"x": 2}, objective_value=0.5, task_count=1)
        self._seed(optimistic, other)
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.2)

        promoted = make_configuration({"x": 1}, objective_value=0.8, task_count=9)
        self.assertTrue(self.experiment.update_measured_configuration(promoted))
        self.assertEqual(self.experiment.get_current_solution().parameters, {"x": 2})
        self.assertEqual(self.experiment.get_current_solution().results["Y1"], 0.5)

    def test_displaced_best_drops_its_warm_start_payload(self):
        optimistic = make_configuration({"x": 1}, objective_value=0.2, task_count=1)
        optimistic.parameter_control_info = {"solutions": [1, 2, 3]}
        other = make_configuration({"x": 2}, objective_value=0.5, task_count=1)
        self._seed(optimistic, other)

        promoted = make_configuration({"x": 1}, objective_value=0.8, task_count=9)
        self.experiment.update_measured_configuration(promoted)
        self.assertEqual(optimistic.parameter_control_info, {})

    def test_parameter_control_record_untouched_when_the_feature_is_off(self):
        # DESCRIPTION declares no Scenario, so parameter control is disabled and
        # the Parameter_control_info record does not exist to be updated.
        rung0 = make_configuration({"x": 1}, objective_value=0.5, task_count=1)
        other = make_configuration({"x": 2}, objective_value=0.4, task_count=1)
        self._seed(rung0, other)

        promoted = make_configuration({"x": 1}, objective_value=0.1, task_count=9)
        self.experiment.update_measured_configuration(promoted)
        collections = [c.kwargs.get("collection_name")
                       for c in self.experiment.database.update_record.call_args_list]
        self.assertNotIn("Parameter_control_info", collections)


if __name__ == "__main__":
    unittest.main()
