import os

from tools.mongo_dao import MongoDB
from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.decorator import MultiTaskLearning
from transfer_learning.multi_task_learning.filters.selector import get_filter


class Standard(MultiTaskLearning):
    def __init__(self, decorator, experiment_description: dict, experiment_id):
        super().__init__(decorator, __name__, experiment_description, experiment_id)
        parameters = self.experiment_description["TransferLearning"][
            "MultiTaskLearning"]["Standard"]
        self.amount_of_configs_to_transfer = parameters["OldNewConfigsRatio"]
        self.transfer_only_best = parameters["TransferBestConfigsOnly"]
        self.most_similar_first = parameters["TransferFromMostSimilarExperimentsFirst"]
        self.transferrable_configurations = []
        self.transferred_configurations = []
        self.few_shot_flag = False
        self.filter = get_filter(parameters["Filters"])
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    def get_data(self, input_data: dict, transferred_data: dict):
        """
        Returns a specified amount of source configurations to be injected into the target surrogate model(s).
        The relative amount of source configurations is defined by the parameter 'OldNewConfigsRatio'
        :return: list of configurations to be transferred
        """
        if len(self.similar_experiments) > 0:
            if len(self.transferrable_configurations) == 0:
                self.__get_all_transferrable_configurations()
            counter = 0
            k = self.amount_of_configs_to_transfer
            self.transferred_configurations = []
            measured_configurations = self.database.get_records_by_experiment_id("Measured_configurations", self.experiment_id)
            while len(self.transferred_configurations) < len(measured_configurations) * k:
                if counter >= len(self.transferrable_configurations):
                    break
                config = self.transferrable_configurations[counter]
                if config.parameters not in [c["Parameters"] for c in measured_configurations] and \
                        config not in self.transferred_configurations:
                    self.transferred_configurations.append(config)
                counter += 1
            self.logger.info(
                f"{len(self.transferred_configurations)} configurations can be transferred to the new model from previous experiments"
                )
        if self.few_shot_flag is True and len(self.transferred_configurations) > 0:
            transferred_data.update({"Best_configuration_to_transfer": self.transferred_configurations[0]})
        else:
            transferred_data.update({"Configurations_to_transfer": self.transferred_configurations})
        return transferred_data

    def __get_all_transferrable_configurations(self):
        """
        Extracts all transferrable source configurations
        :return: list of transferrable configurations
        """
        all_samples = []
        for experiment in self.similar_experiments:
            all_samples.extend(experiment["Samples"])
        inputs = {"FewShotFlag": False, "Data": all_samples}
        result = self.filter.construct_transferred_data(self, inputs)
        self.few_shot_flag = result["FewShotFlag"]
        for sample in result["Data"]:
            c = Configuration(sample["parameters"], Configuration.Type.TRANSFERRED, self.experiment_id)
            c.results = sample["result"]
            self.transferrable_configurations.append(c)
