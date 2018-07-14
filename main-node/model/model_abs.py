from abc import ABC, abstractmethod
class Model(ABC):

    @abstractmethod
    def build_model(self): pass

    @abstractmethod
    def predict_and_validate(self): pass

    @abstractmethod
    def get_new_point(self): pass

    @abstractmethod
    def get_result(self): pass