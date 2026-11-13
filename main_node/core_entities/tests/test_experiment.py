import json
from unittest.mock import MagicMock

import pytest

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.objectives import Objectives


class TestDescriptionForClients:
    """
    Clients of main-node get the search space as the regions of SearchSpace.describe_regions(), so the description
    that is sent to them must not carry Context.SearchSpace as well. The description of the experiment itself must.
    """

    def test_description_has_no_search_space_while_the_experiment_keeps_it(self, get_experiment):
        description, search_space = get_experiment(13)
        experiment = Experiment(description, search_space)

        sent = experiment.get_description_without_search_space()

        assert "SearchSpace" not in sent["Context"]
        assert "SearchSpace" in experiment.description["Context"]

    def test_the_rest_of_the_description_is_unchanged(self, get_experiment):
        description, search_space = get_experiment(13)
        experiment = Experiment(description, search_space)

        sent = experiment.get_description_without_search_space()

        assert set(sent) == set(experiment.description)
        assert set(sent["Context"]) == set(experiment.description["Context"]) - {"SearchSpace"}
        for key in set(sent) - {"Context"}:
            assert sent[key] == experiment.description[key]
        assert sent["Context"]["TaskConfiguration"] == experiment.description["Context"]["TaskConfiguration"]

    def test_description_is_json_serializable(self, get_experiment):
        description, search_space = get_experiment(13)
        experiment = Experiment(description, search_space)

        sent = experiment.get_description_without_search_space()

        assert json.loads(json.dumps(sent)) == sent


def _objective(name: str, minimization: bool) -> dict:
    return {"Name": name, "DataType": "float", "Minimization": minimization,
            "MinExpectedValue": 0, "MaxExpectedValue": float("inf")}


@pytest.fixture
def experiment_with_mixed_directions(get_experiment) -> Experiment:
    """
    An experiment of test case 13 with the objective 'a' minimized and 'b' maximized, whose database and API are mocks.
    """
    description, search_space = get_experiment(13)  # loaded anew for every test
    description["Context"]["TaskConfiguration"]["Objectives"] = {"a": _objective("a", True), "b": _objective("b", False)}
    experiment = Experiment(description, search_space)
    experiment.database, experiment.api = MagicMock(), MagicMock()
    return experiment


def _measured(experiment: Experiment, number: int, results: dict) -> Configuration:
    configuration = Configuration({"parameter": number}, Configuration.Type.TEST, experiment.unique_id)
    configuration.results = results
    configuration.status["measured"] = True
    return configuration


class TestObjectives:

    def test_the_experiment_holds_the_objectives_of_its_description(self, experiment_with_mixed_directions):
        assert experiment_with_mixed_directions.objectives == Objectives.from_description(
            {"a": _objective("a", True), "b": _objective("b", False)})


class TestCurrentBest:
    """A measured configuration replaces the current best unless the best dominates it, each objective in its own direction."""

    @pytest.fixture
    def experiment(self, experiment_with_mixed_directions) -> Experiment:
        experiment_with_mixed_directions.default_configuration = _measured(
            experiment_with_mixed_directions, 0, {"a": 1, "b": 10})
        return experiment_with_mixed_directions

    def test_a_configuration_worse_in_every_objective_does_not_replace_the_best(self, experiment):
        # a is minimized and b maximized: (2, 5) is worse than the default (1, 10) in both
        assert experiment.add_configuration(_measured(experiment, 1, {"a": 2, "b": 5}))

        assert experiment.get_current_solution() is experiment.default_configuration

    def test_a_configuration_better_in_every_objective_replaces_the_best(self, experiment):
        newcomer = _measured(experiment, 1, {"a": 0.5, "b": 20})

        assert experiment.add_configuration(newcomer)

        assert experiment.get_current_solution() is newcomer

    def test_a_configuration_that_does_not_dominate_the_best_replaces_it(self, experiment):
        newcomer = _measured(experiment, 1, {"a": 0.5, "b": 5})  # better in a, worse in b

        assert experiment.add_configuration(newcomer)

        assert experiment.get_current_solution() is newcomer

    def test_a_configuration_without_results_does_not_replace_the_best(self, experiment):
        assert experiment.add_configuration(_measured(experiment, 1, {}))

        assert experiment.get_current_solution() is experiment.default_configuration
