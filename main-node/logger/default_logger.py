import logging
import logging.handlers
import logging.config
import yaml
from yaml.error import YAMLError
import os


class BRISELogConfigurator:

    def __init__(self, config_file="logger/logging_config.yaml"):
        """
        Loads YAML logging configuration file and applies configurations.
        :param config_file: String. Represents path to the configuration file.
        """
        if os.path.exists(config_file):
            # Loading configuration provided in yaml file.
            with open(config_file) as f:
                try:
                    config = yaml.safe_load(f.read())
                except YAMLError as e:
                    config = {'version': 1}
                    logging.error("Unable to read the logging configuration file!"
                                  "An error occurs: %s" % e, exc_info=True)
                    logging.basicConfig(level=logging.DEBUG)

            debug_log_folder = config['handlers']['debug_file_handler']['filename']
            error_log_folder = config['handlers']['error_file_handler']['filename']
            self.__create_logging_folder(debug_log_folder[:debug_log_folder.rfind("/")])
            self.__create_logging_folder(error_log_folder[:error_log_folder.rfind("/")])

            self.__configure_logging(dict_configuration=config)

        else:
            # Using default configuration.
            logging.error("Unable to locate a logging configuration file!")
            logging.basicConfig(level=logging.DEBUG)

    @staticmethod
    def __configure_logging(dict_configuration):
        """
        Configuring logging system according to provided configuration in dictionary/
        :param dict_configuration: Python Dict. according to
        https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig
        :return: Bool True if success, false in other case.
        """
        try:
            logging.config.dictConfig(dict_configuration)
            return True
        except ValueError as e:
            logging.error("Unable to configure the logging system!"
                          "An error occurs: %s" % e, exc_info=True)
            logging.basicConfig(level=logging.DEBUG)
            return False

    @staticmethod
    def get_logger(name):
        """
        Returns logger object with provided name.
        :param name: String, representing logger name.
        :return: Logger object.
        """
        return logging.getLogger(name)

    @staticmethod
    def __create_logging_folder(path):
        """
        Creates folder with logs
        :param path: String. Represents folder path where logs are stored.
        :return:
        """
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except TypeError:
                if os.path.isdir(path):
                    pass
                else:
                    os.makedirs(path)


if __name__ == "__main__":
    def a(logger):
        logger.info("info")
        logger.debug("info")
        logger.warning("info")
        logger.error("info")
        logger.critical("info")
        b()

    def b():
        logger = logging.getLogger(__name__)
        logger.info("info")
        logger.debug("info")
        logger.warning("info")
        logger.error("info")
        logger.critical("info")

    logger = BRISELogConfigurator("logging_config.yaml").get_logger(__name__)
    a(logger)
