import logging
import logging.handlers
from logging import Logger


class BRISELogger(Logger):

    def __init__(self, name_of_logger, global_config):

        super().__init__(name_of_logger)
        logger = Logger(name_of_logger)

        # Basic configuration for log records structure, level of logging.
        formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(name)s |> %(message)s",
                                      datefmt="%d.%m.%Y %H:%M:%S")


        # Creating logger instance.
        # logger = logging.getLogger(name_of_logger)
        logger.setLevel(global_config["logging_level"])

        # Creating handler for sending log messages to console, by default.
        log_to_console_handler = logging.StreamHandler()
        log_to_console_handler.setFormatter(formatter)
        log_to_console_handler.setLevel(global_config["logging_level"])
        logger.addHandler(log_to_console_handler)

        # In case of specified name of file to write logs - creating Handler,
        # that will be added to logger to write logs also to file.
        log_file_name = global_config["results_storage"] + global_config["log_filename"] if global_config["log_filename"] else None
        if log_file_name:
            log_file_handler = logging.handlers.RotatingFileHandler(filename=log_file_name, mode='a', maxBytes=10000000, backupCount=3)
            log_file_handler.setFormatter(formatter)
            log_file_handler.setLevel(global_config["logging_level"])
            logger.addHandler(log_file_handler)

        self.logger = logger



