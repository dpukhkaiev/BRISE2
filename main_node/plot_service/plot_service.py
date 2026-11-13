import optuna 
import plotly
import numpy as np
import scipy.sparse
import scipy.sparse.linalg

from core_entities.experiment import Experiment

CONTOUR_POINT_NUM = 100

FloatDistribution = optuna.distributions.FloatDistribution
IntDistribution = optuna.distributions.IntDistribution
CategoricalDistribution = (
    optuna.distributions.CategoricalDistribution
)
create_trial = optuna.trial.create_trial


def parameter_specs(search_space):
    """
    The specs of all parameters of the search space as {full parameter name: spec}, where a spec is a parameter of
    SearchSpace.describe_regions().
    """
    return {parameter["Name"]: parameter
            for region in search_space.describe_regions() for parameter in region["Parameters"]}


def build_distributions(specs, inactive_parameters=()):
    """
    The distribution of every parameter. The distribution of an inactive parameter also covers the parameter's
    inactive value: a range extended down to it, or one more choice.
    """
    distributions = {}

    for param_name, param_data in specs.items():
        hp_type = param_data.get("Type")
        inactive = param_name in inactive_parameters

        # FLOAT
        if hp_type == "FloatHyperparameter":
            distributions[param_name] = FloatDistribution(
                low=param_data["Inactive"] if inactive else param_data["Lower"],
                high=param_data["Upper"]
            )

        # INT
        elif hp_type == "IntegerHyperparameter":

            distributions[param_name] = IntDistribution(
                low=param_data["Inactive"] if inactive else param_data["Lower"],
                high=param_data["Upper"]
            )

        # ORD / NOM
        elif hp_type in [
            "OrdinalHyperparameter",
            "NominalHyperparameter"
        ]:
            distributions[param_name] = (
                CategoricalDistribution(
                    choices=param_data["Categories"] + [param_data["Inactive"]] if inactive else param_data["Categories"]
                )
            )

    return distributions


def build_directions(objectives):
    return ["minimize" if objective.minimization else "maximize" for objective in objectives]


def reconstruct_study(payload, search_space, objectives, requested_parameters=()):
    """
    The study of the trials of the payload. A requested parameter that some trial lacks is inactive in that trial: the
    trial gets the parameter's inactive value, and the parameter's distribution covers it in every trial.
    """
    directions = build_directions(objectives)

    specs = parameter_specs(search_space)

    inactive_parameters = [
        name for name in requested_parameters
        if any(name not in t["configurations"] for t in payload["trials"])
    ]

    distributions = build_distributions(specs, inactive_parameters)

    # CREATE STUDY
    if len(directions) == 1:
        study = optuna.create_study(
            direction=directions[0]
        )
    else:
        study = optuna.create_study(
            directions=directions
        )

    # ADD TRIALS
    for t in payload["trials"]:
        params = dict(t["configurations"])
        for name in inactive_parameters:
            params.setdefault(name, specs[name]["Inactive"])

        objective_values = [
            float(t["results"][name])
            for name in objectives.names
        ]

        # in a hierarchical search space a trial holds only the parameters of its activated regions
        trial_distributions = {}
        for name in params:
            trial_distributions[name] = distributions[name]

        frozen_trial = create_trial(
            params=params,
            distributions=trial_distributions,
            values=objective_values
        )

        study.add_trial(frozen_trial)

    return study
    
    
# created from Optuna implementation
# https://optuna.readthedocs.io/en/v4.3.0/_modules/optuna/visualization/matplotlib/_contour.html
def interpolate_zmap(
    zmap: dict[tuple[int, int], float],
    width: int,
    height: int,
) -> np.ndarray:
    n = width * height
    a_data = []
    a_row = []
    a_col = []
    b = np.zeros(n)

    for y in range(height):
        for x in range(width):
            index = y * width + x
            # observed value
            if (x, y) in zmap:
                a_data.append(1.0)
                a_row.append(index)
                a_col.append(index)
                b[index] = zmap[(x, y)]
                continue

            # missing value (average of neighbouring cells)
            neighbours = []

            if x > 0:
                neighbours.append((x - 1, y))

            if x < width - 1:
                neighbours.append((x + 1, y))

            if y > 0:
                neighbours.append((x, y - 1))

            if y < height - 1:
                neighbours.append((x, y + 1))

            if not neighbours:
                a_data.append(1.0)
                a_row.append(index)
                a_col.append(index)
                continue

            a_data.append(float(len(neighbours)))
            a_row.append(index)
            a_col.append(index)

            for nx, ny in neighbours:
                neighbour_index = ny * width + nx
                a_data.append(-1.0)
                a_row.append(index)
                a_col.append(neighbour_index)

    A = scipy.sparse.csc_matrix(
        (a_data, (a_row, a_col)),
        shape=(n, n),
    )

    z = scipy.sparse.linalg.spsolve(A, b)

    return z.reshape((height, width))


# created from Optuna implementation
# https://optuna.readthedocs.io/en/v4.3.0/_modules/optuna/visualization/matplotlib/_contour.html
def get_axis_values(
    study,
    parameter: str,
    specs,
):
    parameter_search_space = specs.get(parameter)

    if parameter_search_space is None:
        raise ValueError(
            f"Parameter '{parameter}' not found in search space."
        )

    parameter_type = parameter_search_space.get("Type")

    # ORD / CAT
    if (
        parameter_type == "OrdinalHyperparameter"
        or isinstance(parameter_search_space.get("Categories"), list)
    ):
        categories = parameter_search_space["Categories"]
        axis_values = np.arange(
            len(categories),
            dtype=float,
        )

        return axis_values, categories

    # NUM
    trials = [
        trial
        for trial in study.trials
        if trial.state == optuna.trial.TrialState.COMPLETE
        and parameter in trial.params
    ]

    values = np.array(
        [
            float(trial.params[parameter])
            for trial in trials
        ]
    )

    if len(values) == 0:
        raise ValueError(
            f"No values found for parameter '{parameter}'."
        )

    low = np.min(values)
    high = np.max(values)

    axis_values = np.linspace(
        low,
        high,
        CONTOUR_POINT_NUM,
    )

    return axis_values, None


# DIRECTLY CALLABLE FUNCTIONS
def calculate_importances(payload, search_space, objectives):
    allRes = payload["trials"]
    if len(allRes) < 2:
        return {}

    parameters = payload.get("parameters", [])

    study = reconstruct_study(payload, search_space, objectives, parameters)

    objective = payload.get("objective")

    objective_names = objectives.names

    objective_index = objective_names.index(objective)

    # with a custom target, Optuna's default evaluator measures what leads to low values
    sign = objectives.by_name(objective).sign

    importances = optuna.importance.get_param_importances(
        study,
        params=parameters if parameters else None,
        target=lambda trial: sign * trial.values[objective_index]
    )

    return {
        "importances": importances
    }

def calculate_pareto(payload, search_space, objectives):
    study = reconstruct_study(payload, search_space, objectives)

    objective_names = objectives.names

    objective1 = payload["objective1"]
    objective2 = payload["objective2"]

    x_index = objective_names.index(objective1)
    y_index = objective_names.index(objective2)

    all_points = [
        {
            "x": trial.values[x_index],
            "y": trial.values[y_index],
            "params": trial.params,
            "number": trial.number,
        }
        for trial in study.trials
        if trial.state == optuna.trial.TrialState.COMPLETE
    ]

    pareto_points = [
        {
            "x": trial.values[x_index],
            "y": trial.values[y_index],
            "params": trial.params,
            "number": trial.number,
        }
        for trial in study.best_trials
    ]

    return {
        "objective_names": [objective1, objective2],
        "all_points": all_points,
        "pareto_points": pareto_points,
    }
        
def calculate_contour(payload, search_space, objectives):
    allRes = payload["trials"]

    if len(allRes) < 2:
        return {}

    study = reconstruct_study(payload, search_space, objectives)

    param1 = payload["param1"]
    param2 = payload["param2"]
    objective = payload["objective"]

    objective_names = objectives.names

    objective_index = objective_names.index(objective)

    specs = parameter_specs(search_space)

    # get axes
    xi, x_categories = get_axis_values(
        study,
        param1,
        specs,
    )

    yi, y_categories = get_axis_values(
        study,
        param2,
        specs,
    )

    # grid dimensions
    width = len(xi)
    height = len(yi)

    x_is_categorical = (
        x_categories is not None
    )

    y_is_categorical = (
        y_categories is not None
    )

    x_category_indices = None
    y_category_indices = None

    if x_is_categorical:
        x_category_indices = {
            category: index
            for index, category in enumerate(x_categories)
        }

    if y_is_categorical:
        y_category_indices = {
            category: index
            for index, category in enumerate(y_categories)
        }

    # build sparse z map
    zmap = {}

    for trial in study.trials:
        if trial.state != optuna.trial.TrialState.COMPLETE:
            continue

        if (
            param1 not in trial.params
            or param2 not in trial.params
        ):
            continue

        if trial.values is None:
            continue

        x_value = trial.params[param1]
        y_value = trial.params[param2]

        if x_is_categorical:
            x = x_category_indices[x_value]

        else:
            x = int(
                np.argmin(
                    np.abs(xi - float(x_value))
                )
            )

        if y_is_categorical:
            y = y_category_indices[y_value]

        else:
            y = int(
                np.argmin(
                    np.abs(yi - float(y_value))
                )
            )

        z = float(
            trial.values[objective_index]
        )

        zmap[(x, y)] = z

    if len(zmap) < 2:
        return {}

    zi = interpolate_zmap(
        zmap,
        width,
        height,
    )

    contour = {
        "x": xi.tolist(),
        "y": yi.tolist(),
        "z": zi.tolist(),
        "x_name": param1,
        "y_name": param2,
        "objective_name": objective,
    }

    if x_categories is not None:
        contour["x_categories"] = x_categories

    if y_categories is not None:
        contour["y_categories"] = y_categories

    return {
        "contour": contour
    }


class PlotService:
    """
    The plots are computed from the search space and the objectives of the experiment, which main-node holds. A plot
    request carries only what is specific to the plot.
    """

    def calculate_importances(self, payload, experiment: Experiment):
        return calculate_importances(payload, experiment.search_space, experiment.objectives)

    def calculate_pareto(self, payload, experiment: Experiment):
        return calculate_pareto(payload, experiment.search_space, experiment.objectives)

    def calculate_contour(self, payload, experiment: Experiment):
        return calculate_contour(payload, experiment.search_space, experiment.objectives)
