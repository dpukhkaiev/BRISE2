from tools.features_tools import split_features_and_labels
import pytest


G_DATA = [[2900, 32, 122.0],
        [1600, 8, 101.9],
        [2000, 16, 158.1],
        [1900, 2, 399.4],
        [1800, 1, 133.7]]
G_STRUCTURE = ["feature", "feature", "label"]


def test_split_features_and_labels():
    features, labels = split_features_and_labels(data=G_DATA, structure=G_STRUCTURE)
    features_exp = [[2900, 32], [1600, 8], [2000, 16], [1900, 2], [1800, 1]]
    labels_exp = [122.0, 101.9, 158.1, 399.4, 133.7]
    assert features == features_exp
    assert labels == labels_exp

def test_split_features_and_labels_errors():
    data = [[2900, 32, 122.0],
            [1600, 8, 101.9],
            [2000, 158.1],
            [1900, 2, 399.4],
            [1800, 1, 133.7]]
    with pytest.raises(KeyError, message="too few values"):
        split_features_and_labels(data=data, structure=G_STRUCTURE)

    data = [[2900, 32, 122.0],
            [1600, 8, 101.9],
            [2000, 16, 158.1],
            [1900, 2, 399.4, 78],
            [1800, 1, 133.7]]
    with pytest.raises(KeyError, message="too many values"):
        split_features_and_labels(data=data, structure=G_STRUCTURE)

    data = [[2900, 32, 122.0],
            [1600, 8, 101.9],
            (2000, 16, 158.1),
            [1900, 2, 399.4],
            [1800, 1, 133.7]]
    with pytest.raises(KeyError, message="all elemenets of data array must be arrays, not tuples"):
        split_features_and_labels(data=data, structure=G_STRUCTURE)

    data = [[2900, 32, 122.0],
            [1600, 8, 101.9],
            [2000, "15", 158.1],
            [1900, 2, 399.4],
            [1800, 1, 133.7]]
    with pytest.raises(KeyError, message="valus must be int ot float type"):
        split_features_and_labels(data=data, structure=G_STRUCTURE)

    structure = ["feature", "label", "label"]
    with pytest.raises(KeyError, message="too many 'label' fields, must be only one"):
        split_features_and_labels(data=G_DATA, structure=structure)

    structure = ["feature"]
    with pytest.raises(KeyError, message="there is no 'label' field"):
        split_features_and_labels(data=G_DATA, structure=structure)

    structure = ["label"]
    with pytest.raises(KeyError, message="there is no 'feature' field"):
        split_features_and_labels(data=G_DATA, structure=structure)

    structure = ["something", "label"]
    with pytest.raises(KeyError, message="the name of a field does not match with 'feature' or 'label'"):
        split_features_and_labels(data=G_DATA, structure=structure)

    structure = []
    with pytest.raises(KeyError, message="'structure' array is empty"):
        split_features_and_labels(data=G_DATA, structure=structure)

