from model.regression_sweet_spot import RegressionSweetSpot


def get_model(model_creation_config, log_file_name, features, labels):
    """
    Instantiates need prediction model.
    :param model_creation_config: "ModelCreation" dict of parameters from task description file.
    :param log_file_name: String, file where to store results of model creation.
    :param features: list of all currently discovered features.
    :param labels: list of all currently discovered labels.
    :return: Instantiated object of prediction model.
    """



    if model_creation_config["ModelType"] == "regression":
        return RegressionSweetSpot(log_file_name=log_file_name,
                                   test_size=model_creation_config["ModelTestSize"],
                                   features=features,
                                   labels=labels)
    else:
        print("ERROR: Configuration Error - model type not supported.")
        raise KeyError
