from transfer_learning.model_recommendation.mr_orchestrator import ModelRecommendationOrchestrator
from transfer_learning.multi_task_learning.mtl_orchestrator import MultiTaskLearningOrchestrator
from transfer_learning.transfer_expediency_determination.ted_orchestrator import TEDOrchestrator


class TransferLearningOrchestrator:

    def __init__(self, experiment_description: dict, experiment_id: str):
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.similar_experiments = []
        ted_orchestrator = TEDOrchestrator()
        self.ted_module = (
            ted_orchestrator.get_ted_module(self.experiment_description["TransferLearning"]["TransferExpediencyDetermination"],
                                            self.experiment_id))

        self.transfer_submodules = {"Configuration_transfer": None, "Model_transfer": None}
        if "MultiTaskLearning" in self.experiment_description["TransferLearning"].keys():
            self.mtl_orchestrator = MultiTaskLearningOrchestrator()
            self.transfer_submodules["Configuration_transfer"] = (
                self.mtl_orchestrator.get_mtl_module(self.experiment_description, self.experiment_id))
        if "ModelRecommendation" in self.experiment_description["TransferLearning"].keys():
            self.mr_orchestrator = ModelRecommendationOrchestrator()
            self.transfer_submodules["Model_transfer"] = (
                self.mr_orchestrator.get_mr_module(self.experiment_description,
                                                   self.experiment_id))
