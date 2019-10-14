from abc import ABC, abstractclassmethod

class AbstractDefaultConfigurationHandler(ABC):
    @abstractclassmethod
    def get_default_config(self): pass