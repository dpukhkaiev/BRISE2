import os

from tools.mongo_dao import MongoDB
from transfer_learning.transfer_expediency.transfer_expediency_analyser import TransferExpediencyAnalyser
from transfer_learning.transfer_learning_selector import get_mr_module, get_mtl_module

class TransferLearningModule:

    def __init__(self, experiment_description: dict, experiment_id: str):
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.similar_experiments = []
        self.isMinimizationExperiment = self.experiment_description["TaskConfiguration"]["ObjectivesMinimization"][
            self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"].index(
                max(self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"]))]

        if "ModelsRecommendation" in self.experiment_description["TransferLearning"].keys():
            self.mr_flag = True
            self.mr_module = get_mr_module(self.experiment_description, self.experiment_id)
        else:
            self.mr_flag = False

        if "MultiTaskLearning" in self.experiment_description["TransferLearning"].keys():
            self.mtl_flag = True
            self.mtl_module = get_mtl_module(self.experiment_description, self.experiment_id)
        else:
            self.mtl_flag = False

        self.experiments_transfer_expediency_analyser = TransferExpediencyAnalyser(self.experiment_description, self.experiment_id)
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    def get_transferred_knowledge(self):
        """
        Orchestrator of the transfer learning functionality.
        Returns all required knowledge to be applied in the target experiment.
        The following steps are made:
        1. Define similar experiments (if they weren't defined yet)
        2. Recommend models' combination (if applicable)
        3. Apply multi-task learning (if applicable)
        4. Transfer models' combination directly (if applicable)
        5. Transfer best configuration directly (if applicable)
        :return: dict. Knowledge to be transferred { knowledge_type : knowledge}
        """
        if not self.experiments_transfer_expediency_analyser.were_similar_experiments_found:
            similar_experiments = self.experiments_transfer_expediency_analyser.analyse_experiments_similarity()
            if len(similar_experiments) > 0:
                if self.mr_flag is True:
                    self.mr_module.update_similar_experiments(similar_experiments)
                if self.mtl_flag is True:
                    self.mtl_module.update_similar_experiments(similar_experiments)
                self.experiments_transfer_expediency_analyser.were_similar_experiments_found = True
            else:
                return {"Recommended_models": None,
                        "Configurations_to_transfer": None,
                        "Models_to_transfer": None,
                        "Best_configuration_to_transfer": None
                        }

        input_data = {}
        transferred_data = {"Recommended_models": None,
                            "Configurations_to_transfer": None,
                            "Models_to_transfer": None,
                            "Best_configuration_to_transfer": None
                            }
        numb_of_measured_configurations = \
            self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_measured_configs"]
        input_data.update({"CurrentIteration": numb_of_measured_configurations})
        if self.mr_flag is True:
            transferred_data = self.mr_module.model_recommendation(input_data, transferred_data)
        if self.mtl_flag is True:
            transferred_data = self.mtl_module.multi_task_learning(input_data, transferred_data)
        return transferred_data
