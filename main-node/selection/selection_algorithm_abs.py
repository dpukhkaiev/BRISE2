__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""

from abc import ABC, abstractclassmethod


class SelectionAlgorithm(ABC):
    @abstractclassmethod
    def get_next_point(self): pass
