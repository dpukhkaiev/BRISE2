from collections import OrderedDict
from typing import Mapping, MutableMapping


def description_selection(description: Mapping) -> MutableMapping:

    result = OrderedDict()
    for hp_name in description:
        description[hp_name]["hyperparameter"].generate(result)

    return result
