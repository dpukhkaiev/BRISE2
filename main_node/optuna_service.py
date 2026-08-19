import optuna 
import plotly
import numpy as np
import scipy.sparse
import scipy.sparse.linalg

CONTOUR_POINT_NUM = 100

FloatDistribution = optuna.distributions.FloatDistribution
IntDistribution = optuna.distributions.IntDistribution
CategoricalDistribution = (
    optuna.distributions.CategoricalDistribution
)
create_trial = optuna.trial.create_trial
    
def build_distributions(search_space):
    distributions = {}

    for param_name, param_data in search_space.items():
        if param_name == "Structure":
            continue
        hp_type = param_data.get("Type")
        
        # FLOAT
        if hp_type == "FloatHyperparameter":
            distributions[param_name] = FloatDistribution(
                low=param_data["Lower"],
                high=param_data["Upper"]
            )

        # INT
        elif hp_type == "IntegerHyperparameter":

            distributions[param_name] = IntDistribution(
                low=param_data["Lower"],
                high=param_data["Upper"]
            )

        # ORD / NOM
        elif hp_type in [
            "OrdinalHyperparameter",
            "NominalHyperparameter"
        ]:
            distributions[param_name] = (
                CategoricalDistribution(
                    choices=param_data["Categories"]
                )
            )

    return distributions


def build_directions(objectives):
    directions = []

    for _, objective in objectives.items():
        if objective["Minimization"] is True:
            directions.append("minimize")
        else:
            directions.append("maximize")

    return directions


def extract_objective_values(objectives_dict):

    return list(objectives_dict.values())


def reconstruct_study(input_data):
    experiment_description = (
        input_data["experiment_description"]
    )

    search_space = (
        experiment_description["Context"]
        ["SearchSpace"]
    )

    objectives = (
        experiment_description["Context"]
        ["TaskConfiguration"]
        ["Objectives"]
    )

    directions = build_directions(objectives)

    distributions = build_distributions(
        search_space
    )

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
    for t in input_data["trials"]:
        params = t["configurations"]

        objective_values = [
            float(value)
            for value in t["results"].values()
        ]

        frozen_trial = create_trial(
            params=params,
            distributions=distributions,
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
    experiment_description,
):
    search_space = (
        experiment_description
        .get("Context", {})
        .get("SearchSpace", {})
        .get(parameter)
    )

    if search_space is None:
        raise ValueError(
            f"Parameter '{parameter}' not found in search space."
        )

    parameter_type = search_space.get("Type")

    # ORD / CAT
    if (
        parameter_type == "OrdinalHyperparameter"
        or isinstance(search_space.get("Categories"), list)
    ):
        categories = search_space["Categories"]
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
def calculate_importances(payload):
    allRes = payload["trials"]
    if len(allRes) < 2:
        return {}

    study = reconstruct_study(payload)

    parameters = payload.get("parameters", [])
    objective = payload.get("objective")

    experiment_description = payload["experiment_description"]

    objective_names = list(
        experiment_description["Context"]
        ["TaskConfiguration"]
        ["Objectives"]
        .keys()
    )

    objective_index = objective_names.index(objective)

    importances = optuna.importance.get_param_importances(
        study,
        params=parameters if parameters else None,
        target=lambda trial: trial.values[objective_index]
    )

    return {
        "importances": importances
    }

def calculate_pareto(payload):
    study = reconstruct_study(payload)

    experiment_description = payload["experiment_description"]

    objective_names = list(
        experiment_description["Context"]
        ["TaskConfiguration"]
        ["Objectives"]
        .keys()
    )

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
        
def calculate_contour(payload):
    allRes = payload["trials"]

    if len(allRes) < 2:
        return {}

    study = reconstruct_study(payload)

    param1 = payload["param1"]
    param2 = payload["param2"]
    objective = payload["objective"]

    experiment_description = payload["experiment_description"]

    objective_names = list(
        experiment_description
        ["Context"]
        ["TaskConfiguration"]
        ["Objectives"]
        .keys()
    )

    objective_index = objective_names.index(objective)

    # get axes
    xi, x_categories = get_axis_values(
        study,
        param1,
        experiment_description,
    )

    yi, y_categories = get_axis_values(
        study,
        param2,
        experiment_description,
    )

    # grid dimensions
    width = len(xi)
    height = len(yi)

    # convert trial values into axis coordinates
    search_space = (
        experiment_description
        ["Context"]
        ["SearchSpace"]
    )

    x_search_space = search_space[param1]
    y_search_space = search_space[param2]

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

    print("xi:", len(xi), np.isfinite(xi).all())
    print("yi:", len(yi), np.isfinite(yi).all())
    print("zi:", zi.shape, np.isfinite(zi).all())
    print("nan:", np.isnan(zi).sum())
    print("inf:", np.isinf(zi).sum())

    return {
        "contour": contour
    }
