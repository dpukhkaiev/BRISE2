import shuffle

from transfer_learning.multi_task_learning.filters.decorator import Filter


class Shuffle(Filter):
    def __init__(self, decorator):
        super().__init__(decorator, __name__)

    def filter_data(self, input_data, transferred_data: dict):
        """
        Shuffles list of configurations for transferring.
        :return: shuffled list of configurations.
        """
        shuffle(transferred_data["Data"])
        return transferred_data
