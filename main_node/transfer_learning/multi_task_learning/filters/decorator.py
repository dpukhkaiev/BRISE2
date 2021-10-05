import logging

class FilterBase:
    def filter_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def filter(self, input_data, transferred_data):
        result = self.construct_transferred_data(input_data, transferred_data)
        return result


class Filter(FilterBase):
    def __init__(self, decorator, name):
        self.decorator = decorator
        self.logger = logging.getLogger(name)

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        transferred_data = self.filter_data(input_data, transferred_data)
        transferred_data = self.decorator.construct_transferred_data(input_data, transferred_data)
        return transferred_data
