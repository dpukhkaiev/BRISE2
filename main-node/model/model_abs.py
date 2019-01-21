from abc import ABC, abstractmethod


class Model(ABC):
    @abstractmethod
    def build_model(self): pass

    @abstractmethod
    def validate_model(self): pass

    @abstractmethod
    def predict_solution(self):
        # TODO: Make it `template method`.
        pass
    
    @abstractmethod
    def add_data(self): pass
