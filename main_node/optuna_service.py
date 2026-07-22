import optuna 
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

        params = t["parameters"]

        objective_values = extract_objective_values(
            t["objectives"]
        )

        # SINGLE OBJECTIVE
        if len(objective_values) == 1:

            frozen_trial = create_trial(
                params=params,
                distributions=distributions,
                value=objective_values[0]
            )

        # MULTI OBJECTIVE
        else:

            frozen_trial = create_trial(
                params=params,
                distributions=distributions,
                values=objective_values
            )

        study.add_trial(frozen_trial)

    return study
    
# directly callable functions    
def calculate_importances(allRes):
    print("allRes in calculate_importances:", allRes)
    if not allRes["trials"]:
        return {}
    study = reconstruct_study(allRes)

    importances = (
        optuna.importance.get_param_importances(study)
    )
    print("importances: ", importances)
    return {
        "importances":
            importances
    }

def calculate_pareto(allRes):
    return 0
