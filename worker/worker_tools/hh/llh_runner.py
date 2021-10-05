from __future__ import annotations

import abc
import logging
import os
from typing import List, Mapping

from worker_tools.mongo_dao import MongoDB


class LLHRunner:
    # LLHRunner states
    IDLE = 0
    BUILT_SUCCESS = 1
    RUN_FAILED = 2
    RUN_SUCCESS = 3

    def __init__(self, task: Mapping, llh_wrapper: ILLHWrapper):
        self.logger = logging.getLogger(__name__)
        self._task = task
        self._llh = None
        self._initial_solutions: List = []
        self._hyperparameters: Mapping = {}
        self.report: Mapping = {}
        self._llh_wrapper = llh_wrapper
        self.status = LLHRunner.IDLE
        self.dao = MongoDB(
            mongo_host=os.getenv("BRISE_DATABASE_HOST"),
            mongo_port=int(os.getenv("BRISE_DATABASE_PORT")),
            database_name=os.getenv("BRISE_DATABASE_NAME"),
            user=os.getenv("BRISE_DATABASE_USER"),
            passwd=os.getenv("BRISE_DATABASE_PASS")
        )

    def build(self) -> None:
        """
        Fetches the warming-up information from the database, and delegates the call
        for meta-heuristic construction and run preparation to the LLH wrapper object.

        Updates itself state to BUILT_SUCCESS if wrapper did not raise the exceptions, which is indicates that
        LLH is ready to run.

        :return: None
        """
        self.logger.debug("Fetching warm startup info.")
        wsi_record = self.dao.get_last_record_by_experiment_id("warm_startup_info", self._task["experiment_id"])
        if not wsi_record:
            wsi = None
            self.logger.warning(f"Solving optimization problem from scratch, since no starting solutions available for "
                                f"experiment with ID: {self._task['experiment_id']}.")
        else:
            wsi = wsi_record["wsi"]
        self.logger.debug("Constructing the LLH algorithm.")
        self._llh_wrapper.construct(self._task['parameters'], self._task['Scenario'], wsi)
        self.logger.debug("The LLH algorithm construction succeed.")
        self.status = LLHRunner.BUILT_SUCCESS

    def execute(self) -> None:
        """
        Delegates the LLH execution and results reporting to LLH wrapper.
        :return:
        """
        if self.status != LLHRunner.BUILT_SUCCESS:
            self.logger.error(f"LLH is not ready to be run. Status code: {self.status}.")
        else:
            self.logger.debug("Executing the LLH.")
            self.report = self._llh_wrapper.run_and_report()
            self.status = LLHRunner.RUN_SUCCESS
            self.logger.debug("LLH execution succeed.")


class ILLHWrapper(abc.ABC):
    def __init__(self, problem_type=None):
        self.logger = logging.getLogger(__name__)
        self.warm_startup_info = {}
        self._llh_algorithm = None

    @abc.abstractmethod
    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def run_and_report(self) -> Mapping:
        raise NotImplementedError
