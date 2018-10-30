import logging

def get_model(model_config, log_file_name, task_config=None):
    """
    Instantiates need prediction model.
    :param model_config: Dict. "ModelConfiguration" dict of parameters from task description file.
    :param log_file_name: String, file where to store results of model creation.
    :param task_config: Dict. Describes task configuration including search space.
    :return: Instantiated object of prediction model.
    """
    logger = logging.getLogger(__name__)
    if model_config["ModelType"] == "regression":
        from model.regression_sweet_spot import RegressionSweetSpot
        logger.info("Regression Sweet Spot prediction model selected.")
        return RegressionSweetSpot(log_file_name=log_file_name,
                                   model_config=model_config)
    if model_config["ModelType"] == "BO":
        from model.bayesian_optimization import BayesianOptimization
        logger.info("Bayesian Optimization prediction model selected.")
        return BayesianOptimization(task_config)
    else:
        logger.error("Configuration error - model type not supported: %s" % model_config["ModelType"])
        raise KeyError
