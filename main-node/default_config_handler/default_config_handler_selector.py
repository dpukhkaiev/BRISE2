import logging
        
def get_default_config_handler(experiment):    
    """ This method returns an instance of default configuration handler for current experiment
    
    :rtype:DefaultConfigurationHandler
    """
    logger = logging.getLogger(__name__)
    handler_name = experiment.description["DomainDescription"]["DefaultConfigurationHandler"] \
        if  "DefaultConfigurationHandler" in experiment.description["DomainDescription"] else None

    if len(experiment.description["DomainDescription"]["DefaultConfiguration"]) == \
        len(experiment.description["DomainDescription"]["ParameterNames"]):
        from default_config_handler.default_config_handler import DefaultConfigurationHandler
        config_handler = DefaultConfigurationHandler(experiment)
    elif handler_name == "Automodel":
        # currently Automodel supports only RandomForest among those ML algorithms that are processed by Brise
        if experiment.description["TaskConfiguration"]["TaskName"] == "randomForest":
            from default_config_handler.automodel_default_config_handler import AutomodelDefaultConfigurationHandler
            config_handler = AutomodelDefaultConfigurationHandler(experiment)
            logger.info("RapidMiner Automodel will be used to define default configuration")
        else:
            from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler
            config_handler = RandomDefaultConfigurationHandler(experiment)
            logger.warning("It seems that Automodel is not supported for your experiment -"\
                    " random default configuration will be picked instead!")
    else:
        from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler
        config_handler = RandomDefaultConfigurationHandler(experiment)
        logger.warning("Default configuration is not specified or specified incorrectly!")
    return config_handler
