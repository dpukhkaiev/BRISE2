from typing import List

import pytest

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.few_shot import FewShotDecorator
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.only_best import OnlyBestDecorator


class SourceConfigurations(MultiTaskLearning):
    """The configurations of a source experiment, as the base of a decorator."""

    def __init__(self, experiment_description: dict, configurations: List[Configuration]):
        super().__init__(experiment_description, "experiment")
        self.configurations = configurations

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        return self.configurations


def _configurations(*results: float) -> List[Configuration]:
    configurations = []
    for index, result in enumerate(results):
        configuration = Configuration({"parameter": index}, Configuration.Type.TEST, "source")
        configuration.results = {"Y1": result}
        configurations.append(configuration)
    return configurations


@pytest.fixture(params=[True, False], ids=["minimized", "maximized"])
def minimization(request) -> bool:
    return request.param


@pytest.fixture
def description(get_experiment, minimization) -> dict:
    # test_case_11 has the single objective Y1, maximized
    description, _ = get_experiment(11)
    description["Context"]["TaskConfiguration"]["Objectives"]["Y1"]["Minimization"] = minimization
    return description


class TestFewShotDecorator:

    def test_the_best_configuration_by_the_direction_of_the_objective_is_transferred(self, description, minimization):
        configurations = _configurations(30, 10, 50, 20)
        decorator = FewShotDecorator(description, "experiment", SourceConfigurations(description, configurations))

        transferred = decorator.transfer_configurations([])

        assert [c.results["Y1"] for c in transferred] == ([10] if minimization else [50])


class TestOnlyBestDecorator:

    def test_the_configurations_not_worse_than_the_average_are_transferred(self, description, minimization):
        configurations = _configurations(20, 10, 30)  # average 20, equal to the first
        decorator = OnlyBestDecorator(description, "experiment", SourceConfigurations(description, configurations))

        transferred = decorator.transfer_configurations([])

        assert [c.results["Y1"] for c in transferred] == ([20, 10] if minimization else [20, 30])
