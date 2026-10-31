import json

from core_entities.experiment import Experiment


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
