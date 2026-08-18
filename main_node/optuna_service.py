import optuna 
import plotly
import numpy as np
from optuna.importance import PedAnovaImportanceEvaluator
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

        # ----------------------------------------------------
        # FLOAT
        # ----------------------------------------------------

        if hp_type == "FloatHyperparameter":

            distributions[param_name] = FloatDistribution(
                low=param_data["Lower"],
                high=param_data["Upper"]
            )

        # ----------------------------------------------------
        # INTEGER
        # ----------------------------------------------------

        elif hp_type == "IntegerHyperparameter":

            distributions[param_name] = IntDistribution(
                low=param_data["Lower"],
                high=param_data["Upper"]
            )

        # ----------------------------------------------------
        # ORDINAL / NOMINAL
        # ----------------------------------------------------

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


# ============================================================
# BUILD OPTIMIZATION DIRECTIONS
# ============================================================

def build_directions(objectives):

    directions = []

    for _, objective in objectives.items():

        if objective["Minimization"] is True:
            directions.append("minimize")
        else:
            directions.append("maximize")

    return directions


# ============================================================
# EXTRACT OBJECTIVE VALUES
# ============================================================

def extract_objective_values(objectives_dict):

    return list(objectives_dict.values())


# ============================================================
# RECONSTRUCT OPTUNA STUDY
# ============================================================

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

    # --------------------------------------------------------
    # CREATE STUDY
    # --------------------------------------------------------

    if len(directions) == 1:

        study = optuna.create_study(
            direction=directions[0]
        )

    else:

        study = optuna.create_study(
            directions=directions
        )

    # --------------------------------------------------------
    # ADD TRIALS
    # --------------------------------------------------------

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
    
def interpolate_zmap(
    zmap: dict[tuple[int, int], float],
    width: int,
    height: int,
) -> np.ndarray:
    """
    Optuna-style interpolation of missing values using
    the discrete Poisson equation.
    """

    n = width * height

    a_data = []
    a_row = []
    a_col = []

    b = np.zeros(n)

    for y in range(height):
        for x in range(width):

            index = y * width + x

            # Observed value
            if (x, y) in zmap:
                a_data.append(1.0)
                a_row.append(index)
                a_col.append(index)

                b[index] = zmap[(x, y)]

                continue

            # Missing value:
            # average of neighbouring cells
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


def get_axis_values(
    study,
    parameter: str,
    experiment_description,
):
    """
    Creates the contour axis for one parameter.

    Returns:
        axis_values:
            Numerical values used by Plotly.

        parameter_values:
            Original parameter values corresponding to the axis.
    """

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

    # ---------------------------------------------------------
    # Ordinal / categorical
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Numerical
    # ---------------------------------------------------------

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

    # Use a 100-point continuous axis
    axis_values = np.linspace(
        low,
        high,
        CONTOUR_POINT_NUM,
    )

    return axis_values, None

# directly callable functions    
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
        evaluator=PedAnovaImportanceEvaluator(),
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

    # ---------------------------------------------------------
    # Get axes
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Determine grid dimensions
    # ---------------------------------------------------------

    width = len(xi)
    height = len(yi)

    # ---------------------------------------------------------
    # Convert trial values into axis coordinates
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Build sparse z map
    # ---------------------------------------------------------

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

        # -----------------------------
        # X coordinate
        # -----------------------------

        if x_is_categorical:
            x = x_category_indices[x_value]

        else:
            x = int(
                np.argmin(
                    np.abs(xi - float(x_value))
                )
            )

        # -----------------------------
        # Y coordinate
        # -----------------------------

        if y_is_categorical:
            y = y_category_indices[y_value]

        else:
            y = int(
                np.argmin(
                    np.abs(yi - float(y_value))
                )
            )

        # -----------------------------
        # Objective
        # -----------------------------

        z = float(
            trial.values[objective_index]
        )

        zmap[(x, y)] = z

    if len(zmap) < 2:
        return {}

    # ---------------------------------------------------------
    # Interpolate
    # ---------------------------------------------------------

    zi = interpolate_zmap(
        zmap,
        width,
        height,
    )

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    contour = {
        "x": xi.tolist(),
        "y": yi.tolist(),
        "z": zi.tolist(),
        "x_name": param1,
        "y_name": param2,
        "objective_name": objective,
    }

    # Optional category information
    if x_categories is not None:
        contour["x_categories"] = x_categories

    if y_categories is not None:
        contour["y_categories"] = y_categories

    return {
        "contour": contour
    }
