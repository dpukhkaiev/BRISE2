import logging


def get_model(experiment, log_file_name):
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
                                   model_config=experiment.description["ModelConfiguration"])
    elif experiment.description["ModelConfiguration"]["ModelType"] == "BO":
        from model.bayesian_optimization import BayesianOptimization
        logger.info("Bayesian Optimization prediction model selected.")
        return BayesianOptimization(experiment.description)
    else:
        logger.error("Configuration error - model type not supported: %s"
                     % experiment.description["ModelConfiguration"]["ModelType"])
        raise KeyError("Configuration error - model type not supported: %s"
                       % experiment.description["ModelConfiguration"]["ModelType"])
