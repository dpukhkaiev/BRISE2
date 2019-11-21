import logging

from core_entities.experiment import Experiment
from model.model_abs import Model


def get_model(experiment: Experiment, log_file_name: str) -> Model:
    """
    Instantiates need prediction model.
    :param experiment: the instance of Experiment class
    :param log_file_name: String, file where to store results of model creation.
    :return: Instantiated object of prediction model.
    """
    logger = logging.getLogger(__name__)
    if experiment.description["ModelConfiguration"]["ModelType"] == "regression":
        from model.regression_sweet_spot import RegressionSweetSpot
        logger.info("Regression Sweet Spot prediction model selected.")
        return RegressionSweetSpot(log_file_name=log_file_name,
                                   experiment=experiment)
    elif experiment.description["ModelConfiguration"]["ModelType"] == "BO":
        from model.bayesian_optimization import BayesianOptimization
        logger.info("Bayesian Optimization prediction model selected.")
        return BayesianOptimization(experiment)

    else:
        raise KeyError(f'Model {experiment.description["ModelConfiguration"]["ModelType"]} is not supported!')
