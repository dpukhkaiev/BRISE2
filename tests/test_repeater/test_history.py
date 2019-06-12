import pytest
import pickle

from repeater.history import History


def test_default_history():
    def_history = History().history
    assert def_history == {}


def test_get():
    point1 = (2900, 32)
    values1 = [1, 50]
    history1 = History()
    history1.put(point1, values1[0])
    history1.put(point1, values1[1])
    assert history1.get(point1) == values1

    points = [(2400, 2), (0, 1), (500, 25), (1900, 25), (2900, 50)]
    values = [[45, 68, 56], [567, 345.7], 56, [98.25, 70], [45.8, 78]]
    history1 = History()
    for p, v in zip(points, values):
        history1.put(p, v)
    for index, value in enumerate(values):
        value = [value]
        assert history1.get(points[index]) == value

    point = (1, 1)
    assert history1.get(point) == []


def test_put():

    point1 = (2900, 32)
    values1 = [1, 50]
    history1 = History()
    history1.put(point1, values1[0])
    history1.put(point1, values1[1])
    assert history1.history[str(point1)] == values1
    history1.history = {}

    points = [[2900.0, 16], (2900, 32), (3000, 48), "123", 0, (3000, 32), [2900, 32], (2500, 15), [2900.0, 16]]
    values = [50, "yui", "ret", 5, [55, 48.9, 99], 1, ["123", 123], [], ['suppa', 'result', None, 123]]

    # Since each new value (result) is adding to the end of values list for these configuration.
    # Also covers testing of proper types storing.
    for point, value in zip(points, values):
        history1.put(point, value)
        assert value == history1.history[str(point)][-1]

    assert len(history1.history[str([2900.0, 16])]) == 2


def make_history_object():
    # Supporting function for preparing valid history object with some data in it.
    # Testing data - 6 configurations, 5 unique, 6 results.
    history_my = History()
    points = [(2900, 32), (3000, 48), (3000, 32), (2900, 30), (2900, 16), (2900, 30)]
    values = [50, 5, [55, 48, 99], 1, [123.98, 123], ['string value', 223, 23.1, '32', '32.4', None]]
    for p, v in zip(points, values):
        history_my.put(p, v)
    return history_my


def test_dump(tmpdir):

    history_my = make_history_object()

    file_path = tmpdir.join('file.hist')     # pathToHistory/ folder should also be created.
    assert history_my.dump(str(file_path)) is True   # Check storing in normal case.
    with open(str(file_path), 'rb') as f:
        assert pickle.loads(f.read()) == history_my.history

    #   Verification of problem cases with creating (writing) to write-protected files
    # is too complicated (cause 1. New file will be created. 2. It will be created from 'root' user
    # that will ensure highest read-write permissions to FS IO.


def test_load(tmpdir):

    # Preparing data.
    history_obj = make_history_object()
    history_to_be_written = history_obj.history.copy()

    file_path = tmpdir.join('file.hist')
    with open(str(file_path), "wb") as f:
        pickle.dump(history_to_be_written, f)

    # Test proper loading without dropping previous data using "flush" flag.
    history_obj.history.clear()
    assert history_obj.load(str(file_path))
    assert history_obj.history == history_to_be_written

    # Test proper loading with dropping previous data using "flush" flag.
    assert history_obj.load(str(file_path), flush=True)
    assert history_obj.history == history_to_be_written

    # Testing invalid dumped invalid file.
    with open(str(file_path), "w") as f:
        f.write(str(history_to_be_written))

    history_obj.history = {'key': 'value'}
    assert history_obj.load(str(file_path)) is False
    assert history_obj.history == {'key': 'value'}
    assert history_obj.load(str(file_path), flush=True) is False
    assert history_obj.history == {'key': 'value'}
