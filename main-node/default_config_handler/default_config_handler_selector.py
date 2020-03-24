import logging

from core_entities.experiment import Experiment
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler


def get_default_config_handler(experiment: Experiment) -> AbstractDefaultConfigurationHandler:
    """ This method returns an instance of default configuration handler for current experiment
    
    :rtype:DefaultConfigurationHandler
    """
    logger = logging.getLogger(__name__)
    handler_name = experiment.description["DomainDescription"]["DefaultConfigurationHandler"] \
        if "DefaultConfigurationHandler" in experiment.description["DomainDescription"] else None

    if experiment.search_space.get_default_configuration() and \
            len(experiment.search_space.get_default_configuration().parameters) == \
            len(experiment.search_space.get_hyperparameter_names()):
        from default_config_handler.default_config_handler import DefaultConfigurationHandler
        config_handler = DefaultConfigurationHandler(experiment)
    else:
        from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler
        config_handler = RandomDefaultConfigurationHandler(experiment)
        logger.warning("Default configuration is not specified or specified incorrectly!")
    return config_handler
