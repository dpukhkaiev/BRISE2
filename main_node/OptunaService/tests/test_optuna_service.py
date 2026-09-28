from OptunaService import optuna_service

ALGORITHM = "Context.SearchSpace.Algorithm"
ALPHA = "Context.SearchSpace.Algorithm.A.alpha"
BETA = "Context.SearchSpace.Algorithm.A.beta"
GAMMA = "Context.SearchSpace.Algorithm.B.gamma"


def hierarchical_experiment_description():
    # Algorithm activates either region A (alpha, beta) or region B (gamma)
    return {
        "Context": {
            "TaskConfiguration": {
                "Objectives": {
                    "Y1": {"Name": "Y1", "DataType": "float", "Minimization": True}
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


class TestOptunaService:

    def test_nested_parameters_are_named_by_their_activation_path(self):
        search_space = hierarchical_experiment_description()["Context"]["SearchSpace"]

        normalized = optuna_service.normalize_search_space(search_space)

        assert list(normalized.keys()) == [ALGORITHM, ALPHA, BETA, GAMMA]

    def test_each_trial_gets_only_the_distributions_of_its_active_parameters(self):
        payload = {
            "experiment_description": hierarchical_experiment_description(),
            "trials": region_a_trials() + region_b_trials()
        }

        study = optuna_service.reconstruct_study(payload)

        assert len(study.trials) == 15
        for trial in study.trials:
            assert set(trial.distributions.keys()) == set(trial.params.keys())

    def test_contour_is_built_for_parameters_of_a_nested_region(self):
        payload = {
            "experiment_description": hierarchical_experiment_description(),
            "trials": region_a_trials() + region_b_trials(),
            "param1": ALPHA,
            "param2": BETA,
            "objective": "Y1"
        }

        result = optuna_service.calculate_contour(payload)

        assert result["contour"]["x_name"] == ALPHA
        assert result["contour"]["y_name"] == BETA
        assert len(result["contour"]["z"]) == len(result["contour"]["y"])

    def test_importances_are_computed_for_every_parameter_of_a_nested_region(self):
        payload = {
            "experiment_description": hierarchical_experiment_description(),
            "trials": region_a_trials(),
            "parameters": [ALPHA, BETA],
            "objective": "Y1"
        }

        result = optuna_service.calculate_importances(payload)

        assert set(result["importances"].keys()) == {ALPHA, BETA}
