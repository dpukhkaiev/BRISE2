import pytest
from optuna.distributions import CategoricalDistribution, FloatDistribution, IntDistribution

from core_entities.experiment import Experiment
from core_entities.objectives import Objectives
from core_entities.search_space import SearchSpace
from plot_service import plot_service
from plot_service.plot_service import PlotService

ALGORITHM = "Context.SearchSpace.Algorithm"
ALPHA = "Context.SearchSpace.Algorithm.A.alpha"
BETA = "Context.SearchSpace.Algorithm.A.beta"
GAMMA = "Context.SearchSpace.Algorithm.B.gamma"

N0 = "Context.SearchSpace.N0"
F1 = "Context.SearchSpace.N0.N02.F1"


def objectives_of(**minimization: bool) -> Objectives:
    """Objectives named after the keywords, in their order, minimized or maximized as given."""
    return Objectives.from_description({
        name: {"Name": name, "DataType": "float", "Minimization": minimized,
               "MinExpectedValue": 0, "MaxExpectedValue": float("inf")}
        for name, minimized in minimization.items()})


def hierarchical_experiment_description():
    # Algorithm activates either region A (alpha, beta) or region B (gamma)
    return {
        "Context": {
            "TaskConfiguration": {
                "Objectives": {
                    "Y1": {"Name": "Y1", "DataType": "float", "Minimization": True,
                           "MinExpectedValue": 0, "MaxExpectedValue": float("inf")}
                }
            },
            "SearchSpace": {
                "Algorithm": {
                    "Type": "NominalHyperparameter",
                    "Level": 0,
                    "Categories": [f"{ALGORITHM}.A", f"{ALGORITHM}.B"],
                    "Default": f"{ALGORITHM}.A",
                    "A": {
                        "Type": "Category",
                        "alpha": {"Type": "FloatHyperparameter", "Level": 1, "Lower": 0.0, "Upper": 1.0, "Default": 0.5},
                        "beta": {"Type": "IntegerHyperparameter", "Level": 1, "Lower": 1, "Upper": 10, "Default": 5}
                    },
                    "B": {
                        "Type": "Category",
                        "gamma": {"Type": "FloatHyperparameter", "Level": 1, "Lower": 0.0, "Upper": 5.0, "Default": 1.0}
                    }
                },
                "Structure": {"Hierarchical": {}}
            }
        }
    }


def region_a_trials():
    trials = []
    for i in range(10):
        alpha = i / 10
        beta = 1 + i % 5
        trials.append({
            "configurations": {ALGORITHM: f"{ALGORITHM}.A", ALPHA: alpha, BETA: beta},
            "results": {"Y1": alpha * 10 + beta}
        })
    return trials


def region_b_trials():
    trials = []
    for i in range(5):
        gamma = i / 2
        trials.append({
            "configurations": {ALGORITHM: f"{ALGORITHM}.B", GAMMA: gamma},
            "results": {"Y1": gamma}
        })
    return trials


def search_space_and_objectives():
    description = hierarchical_experiment_description()
    return (SearchSpace(description["Context"]["SearchSpace"]),
            Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"]))


class TestPlotCalculation:
    """
    The plots are computed from the SearchSpace and the objectives of the running experiment. A plot payload holds
    only what is specific to the plot: its parameters, objective(s) and the trials.
    """

    def test_parameter_specs_are_named_by_the_search_space(self):
        search_space, _ = search_space_and_objectives()

        specs = plot_service.parameter_specs(search_space)

        assert set(specs) == set(search_space.hp_names) == {ALGORITHM, ALPHA, BETA, GAMMA}
        assert specs[ALPHA]["Type"] == "FloatHyperparameter"
        assert (specs[ALPHA]["Lower"], specs[ALPHA]["Upper"]) == (0.0, 1.0)
        assert specs[ALGORITHM]["Categories"] == [f"{ALGORITHM}.A", f"{ALGORITHM}.B"]

    def test_each_trial_gets_only_the_distributions_of_its_active_parameters(self):
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": region_a_trials()[:1] + region_b_trials()[:1]}

        study = plot_service.reconstruct_study(payload, search_space, objectives)

        region_a_trial, region_b_trial = study.trials
        assert region_a_trial.distributions == {
            ALGORITHM: CategoricalDistribution([f"{ALGORITHM}.A", f"{ALGORITHM}.B"]),
            ALPHA: FloatDistribution(0.0, 1.0),
            BETA: IntDistribution(1, 10),
        }
        assert region_b_trial.distributions == {
            ALGORITHM: CategoricalDistribution([f"{ALGORITHM}.A", f"{ALGORITHM}.B"]),
            GAMMA: FloatDistribution(0.0, 5.0),
        }

    def test_results_are_matched_to_the_objectives_by_name(self):
        search_space, _ = search_space_and_objectives()
        objectives = objectives_of(Y1=True, Y2=True)
        # the results of a trial are not necessarily listed in the order of the objectives
        payload = {"trials": [{"configurations": {ALGORITHM: f"{ALGORITHM}.B", GAMMA: 1.0}, "results": {"Y2": 20.0, "Y1": 10.0}}]}

        study = plot_service.reconstruct_study(payload, search_space, objectives)

        assert study.trials[0].values == [10.0, 20.0]

    def test_contour_axes_cover_the_observed_values_of_numeric_parameters(self):
        search_space, objectives = search_space_and_objectives()
        payload = {
            "trials": region_a_trials() + region_b_trials(),
            "param1": ALPHA,
            "param2": BETA,
            "objective": "Y1"
        }

        contour = plot_service.calculate_contour(payload, search_space, objectives)["contour"]

        assert (contour["x_name"], contour["y_name"]) == (ALPHA, BETA)
        assert (contour["x"][0], contour["x"][-1]) == (0.0, 0.9)
        assert (contour["y"][0], contour["y"][-1]) == (1.0, 5.0)
        assert "x_categories" not in contour and "y_categories" not in contour

    def test_contour_axis_of_a_categorical_parameter_has_one_position_per_category(self):
        search_space, objectives = search_space_and_objectives()
        payload = {
            "trials": region_a_trials() + region_b_trials(),
            "param1": ALGORITHM,
            "param2": ALPHA,
            "objective": "Y1"
        }

        contour = plot_service.calculate_contour(payload, search_space, objectives)["contour"]

        assert contour["x_categories"] == [f"{ALGORITHM}.A", f"{ALGORITHM}.B"]
        assert contour["x"] == [0.0, 1.0]
        # only the trials of region A have alpha
        assert (contour["y"][0], contour["y"][-1]) == (0.0, 0.9)
        assert len(contour["z"]) == len(contour["y"]) and len(contour["z"][0]) == len(contour["x"])

    def test_contour_of_a_parameter_outside_the_search_space_fails(self):
        search_space, objectives = search_space_and_objectives()
        payload = {
            "trials": region_a_trials(),
            "param1": ALPHA,
            "param2": "Context.SearchSpace.Missing",
            "objective": "Y1"
        }

        with pytest.raises(ValueError):
            plot_service.calculate_contour(payload, search_space, objectives)

    def test_importances_rank_the_parameter_with_the_larger_effect_first(self):
        # Y1 = alpha * 10 + beta, so alpha ranges over 9 and beta over 4
        search_space, objectives = search_space_and_objectives()
        payload = {
            "trials": region_a_trials(),
            "parameters": [ALPHA, BETA],
            "objective": "Y1"
        }

        importances = plot_service.calculate_importances(payload, search_space, objectives)["importances"]

        assert set(importances) == {ALPHA, BETA}
        assert importances[ALPHA] > importances[BETA]

    @pytest.mark.parametrize("minimization, most_important", [(True, BETA), (False, ALPHA)])
    def test_importances_describe_what_leads_to_good_values_of_the_objective(self, minimization, most_important):
        # Y1 is 100 for the largest alpha and follows beta otherwise, so the smallest values are reached through
        # beta and the largest ones through alpha
        search_space, _ = search_space_and_objectives()
        objectives = objectives_of(Y1=minimization)
        trials = [{"configurations": {ALGORITHM: f"{ALGORITHM}.A", ALPHA: alpha / 10, BETA: beta},
                   "results": {"Y1": 100.0 if alpha == 9 else float(beta)}}
                  for alpha in range(10) for beta in range(1, 6)]
        payload = {"trials": trials, "parameters": [ALPHA, BETA], "objective": "Y1"}

        importances = plot_service.calculate_importances(payload, search_space, objectives)["importances"]

        assert max(importances, key=importances.get) == most_important

    def test_trial_without_a_requested_parameter_gets_its_inactive_value(self):
        # region A has alpha, region B has gamma: each parameter is inactive in the trials of the other region
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": region_a_trials()[:1] + region_b_trials()[:1]}

        study = plot_service.reconstruct_study(payload, search_space, objectives, requested_parameters=[ALPHA, GAMMA])

        region_a_trial, region_b_trial = study.trials
        assert region_a_trial.params[GAMMA] == -5.0
        assert region_b_trial.params[ALPHA] == -1.0
        assert region_a_trial.params[ALPHA] == 0.0 and region_b_trial.params[GAMMA] == 0.0

    def test_inactive_value_extends_the_distribution_of_every_trial(self):
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": region_a_trials()[:1] + region_b_trials()[:1]}

        study = plot_service.reconstruct_study(payload, search_space, objectives, requested_parameters=[ALPHA, BETA, GAMMA])

        for trial in study.trials:
            assert trial.distributions[ALPHA] == FloatDistribution(-1.0, 1.0)
            assert trial.distributions[BETA] == IntDistribution(-8, 10)
            assert trial.distributions[GAMMA] == FloatDistribution(-5.0, 5.0)

    def test_inactive_value_is_a_further_choice_of_a_categorical_parameter(self):
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": [{"configurations": {ALPHA: 0.5}, "results": {"Y1": 1.0}}]}

        study = plot_service.reconstruct_study(payload, search_space, objectives, requested_parameters=[ALGORITHM])

        assert study.trials[0].params[ALGORITHM] == "inactive"
        assert study.trials[0].distributions[ALGORITHM] == CategoricalDistribution([f"{ALGORITHM}.A", f"{ALGORITHM}.B", "inactive"])

    def test_distribution_is_not_extended_for_a_parameter_that_is_active_in_every_trial(self):
        # the trials of one region of a hierarchical space activate its parameters together
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": region_a_trials()}

        study = plot_service.reconstruct_study(payload, search_space, objectives, requested_parameters=[ALPHA, BETA])

        for trial in study.trials:
            assert trial.distributions[ALPHA] == FloatDistribution(0.0, 1.0)
            assert trial.distributions[BETA] == IntDistribution(1, 10)

    def test_trials_are_left_as_measured_when_no_parameter_is_requested(self):
        search_space, objectives = search_space_and_objectives()
        payload = {"trials": region_a_trials()[:1] + region_b_trials()[:1]}

        study = plot_service.reconstruct_study(payload, search_space, objectives)

        assert set(study.trials[0].params) == {ALGORITHM, ALPHA, BETA}
        assert set(study.trials[1].params) == {ALGORITHM, GAMMA}

    def test_importances_count_the_activation_of_a_parameter_as_part_of_its_effect(self):
        # the best trials are the ones of region B, in which alpha is inactive, so alpha matters as well as gamma
        search_space, objectives = search_space_and_objectives()
        payload = {
            "trials": [{"configurations": {ALGORITHM: f"{ALGORITHM}.A", ALPHA: i / 10}, "results": {"Y1": 10.0 + i}} for i in range(8)]
                      + [{"configurations": {ALGORITHM: f"{ALGORITHM}.B", GAMMA: i / 2}, "results": {"Y1": float(i)}} for i in range(8)],
            "parameters": [ALPHA, GAMMA],
            "objective": "Y1"
        }

        importances = plot_service.calculate_importances(payload, search_space, objectives)["importances"]

        assert importances[ALPHA] > 0 and importances[GAMMA] > 0

    @pytest.mark.parametrize("calculate, payload", [
        (plot_service.calculate_importances, {"parameters": [ALPHA], "objective": "Y1"}),
        (plot_service.calculate_contour, {"param1": ALPHA, "param2": BETA, "objective": "Y1"}),
    ])
    def test_plot_of_fewer_than_two_trials_is_empty(self, calculate, payload):
        search_space, objectives = search_space_and_objectives()

        assert calculate({"trials": region_a_trials()[:1], **payload}, search_space, objectives) == {}

    def test_pareto_front_is_computed_for_the_objectives_of_the_experiment(self):
        search_space, objectives = self._two_objectives()
        payload = {"trials": self._pareto_trials(), "objective1": "Y1", "objective2": "Y2"}

        result = plot_service.calculate_pareto(payload, search_space, objectives)

        assert result["objective_names"] == ["Y1", "Y2"]
        assert len(result["all_points"]) == 4
        assert len(result["pareto_points"]) == 3  # the last trial is dominated

    def test_pareto_axes_follow_the_requested_objectives(self):
        search_space, objectives = self._two_objectives()
        payload = {"trials": self._pareto_trials(), "objective1": "Y2", "objective2": "Y1"}

        result = plot_service.calculate_pareto(payload, search_space, objectives)

        assert result["objective_names"] == ["Y2", "Y1"]
        assert [(point["x"], point["y"]) for point in result["all_points"]] == [(5.0, 0.0), (4.0, 1.0), (3.0, 2.0), (5.0, 5.0)]

    def test_pareto_front_of_a_maximized_objective_prefers_larger_values(self):
        search_space, _ = search_space_and_objectives()
        objectives = objectives_of(Y1=True, Y2=False)
        # Y1 is minimized and Y2 maximized: the first trial has the smallest Y1 and the largest Y2, so it dominates the rest
        payload = {"trials": self._pareto_trials(), "objective1": "Y1", "objective2": "Y2"}

        result = plot_service.calculate_pareto(payload, search_space, objectives)

        assert [point["number"] for point in result["pareto_points"]] == [0]

    @staticmethod
    def _two_objectives():
        search_space, _ = search_space_and_objectives()
        return search_space, objectives_of(Y1=True, Y2=True)

    @staticmethod
    def _pareto_trials():
        # Y1 grows and Y2 shrinks with gamma; the last trial is worse than the others in both
        trials = [
            {"configurations": {ALGORITHM: f"{ALGORITHM}.B", GAMMA: gamma}, "results": {"Y1": gamma, "Y2": 5 - gamma}}
            for gamma in (0.0, 1.0, 2.0)
        ]
        trials.append({"configurations": {ALGORITHM: f"{ALGORITHM}.B", GAMMA: 3.0}, "results": {"Y1": 5.0, "Y2": 5.0}})
        return trials


class TestPlotService:
    """
    A plot request carries only what is specific to the plot. The search space and the objectives come from the
    experiment that main-node holds.
    """

    @staticmethod
    def _trials(objectives):
        return [{"configurations": {N0: f"{N0}.N02", F1: value}, "results": {name: value * 2 for name in objectives}}
                for value in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)]

    @pytest.mark.parametrize("calculate, plot_specific_payload, result_key", [
        ("calculate_importances", {"parameters": [F1]}, "importances"),
        ("calculate_pareto", {}, "pareto_points"),
        ("calculate_contour", {"param1": N0, "param2": F1}, "contour"),
    ])
    def test_every_plot_is_computed_from_the_search_space_and_objectives_of_the_experiment(
            self, get_experiment, calculate, plot_specific_payload, result_key):
        experiment = Experiment(*get_experiment(16))
        objectives = experiment.objectives.names
        payload = {"trials": self._trials(objectives), "objective": objectives[0],
                   "objective1": objectives[0], "objective2": objectives[1], **plot_specific_payload}

        result = getattr(PlotService(), calculate)(payload, experiment)

        assert result[result_key]

    def test_importances_are_reported_for_the_requested_parameters(self, get_experiment):
        experiment = Experiment(*get_experiment(16))
        objectives = experiment.objectives.names
        payload = {"trials": self._trials(objectives), "parameters": [F1], "objective": objectives[0]}

        result = PlotService().calculate_importances(payload, experiment)

        assert set(result["importances"]) == {F1}

    def test_plot_of_a_missing_experiment_fails(self):
        # api-supreme answers any failed plot request with the empty result of the plot
        with pytest.raises(Exception):
            PlotService().calculate_importances({"trials": []}, None)
