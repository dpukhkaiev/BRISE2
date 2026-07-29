import optuna 
from optuna.importance import PedAnovaImportanceEvaluator

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
    
# directly callable functions    
def calculate_importances(payload):
    allRes = payload["trials"]
    if len(allRes) < 2:
        return {}
    study = reconstruct_study(payload)

    importances = (
        optuna.importance.get_param_importances(study, evaluator=PedAnovaImportanceEvaluator())
    )
    return {
        "importances": 
            importances
    }

def calculate_pareto(payload):
    study = reconstruct_study(payload)
    
    objective_names = []
  
    for trial in payload["trials"]:
        if "results" in trial:
            objective_names = list(trial["results"].keys())
            break
        
    all_points = [
        {
            "x": trial.values[0],
            "y": trial.values[1],
            "params": trial.params,
            "number": trial.number,
        }
        for trial in study.trials
        if trial.state == optuna.trial.TrialState.COMPLETE
    ]

    pareto_points = [
        {
            "x": trial.values[0],
            "y": trial.values[1],
            "params": trial.params,
            "number": trial.number,
        }
        for trial in study.best_trials
    ]
    print("all points: ", all_points)
    print("pareto points: ", pareto_points)
    return {
        "objective_names": objective_names,
        "all_points": all_points, 
        "pareto_points": pareto_points
    }
        
def calculate_contour(payload):
    study = reconstruct_study(payload)
    fig = optuna.visualization.plot_contour(study)
    print(fig.data)
    objective_name = next(iter(
        payload["experiment_description"]["Context"]["TaskConfiguration"]["Objectives"]
    ))
    contour = {
        "x": list(fig.data[0].x),
        "y": list(fig.data[0].y),
        "z": fig.data[0].z,
        "x_name": fig.layout.xaxis.title.text,
        "y_name": fig.layout.yaxis.title.text,
        "objective_name": objective_name
    }
    return {"contour": contour}
