import logging
from typing import Optional

from configuration_racing.racing_abs import AbstractRacing
from tools.reflective_class_import import reflective_class_import


class RacingOrchestrator:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_racing(self, experiment_description: dict) -> Optional[AbstractRacing]:
        """
        Returns the Racing strategy declared in the Experiment Description, or None
        when the (optional) Racing feature is absent. A None result keeps the core
        on its default self-clocking loop.

        :param experiment_description: full Experiment Description (dict).
        :return: an AbstractRacing instance, or None.
        """
        racing = experiment_description.get("Racing")
        if not racing:
            return None

        strategy_name = next((key for key in racing
                              if isinstance(racing[key], dict) and "Type" in racing[key]), None)
        if strategy_name is None:
            raise ValueError(f"Racing declares no strategy with a 'Type': {racing}.")
        strategy_type = racing[strategy_name]["Type"]

        strategy_class = reflective_class_import(class_name=strategy_type,
                                                 folder_path="configuration_racing")
        self.logger.info(f"{strategy_name} racing strategy selected.")
        return strategy_class(experiment_description)
