from model.regression_sweet_spot import RegressionSweetSpot
from model.bayesian_optimization import BayesianOptimization


def get_model(model_config, log_file_name, task_config=None):
    """
    Instantiates need prediction model.
    :param model_config: Dict. "ModelConfiguration" dict of parameters from task description file.
    :param log_file_name: String, file where to store results of model creation.
    :param features: list of all currently discovered features.
                     TODO - shape of features
    :param labels: list of all currently discovered labels.
                   TODO - shape of labels
    :param task_config: Dict. Describes task configuration including search space.
    :return: Instantiated object of prediction model.
    """

    if model_config["ModelType"] == "regression":
        return RegressionSweetSpot(log_file_name=log_file_name,
                                   model_config=model_config)
    if model_config["ModelType"] == "BO":
        return BayesianOptimization(task_config)
    else:
        print("ERROR: Configuration Error - model type not supported.")
        raise KeyError
