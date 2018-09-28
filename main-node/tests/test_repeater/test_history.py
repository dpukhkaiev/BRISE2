from repeater.history import History
import pytest


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
    for p,v in zip(points,values):
        history1.put(p, v)
    for index, value in enumerate(values):
        value = [value]
        assert history1.get(points[index]) == value

    point = (1, 1)
    assert history1.get(point) == []


def check_point_is_tuple(point_value):
    if isinstance(point_value, tuple) and (all(isinstance(list_item, int) for list_item in point_value)):
        return True
    else:
        return False


def test_put():
    point1 = (2900, 32)
    values1 = [1, 50]
    history1 = History()
    history1.put(point1, values1[0])
    history1.put(point1, values1[1])
    assert history1.history[str(point1)] == values1
    history1.history = {}

    points = [[2900, 16], (2900, 32), (3000, 48), "123", 0, (3000, 32), [2900, 32], (2500, 15)]
    values = [50, "yui", "ret", 5, [55, 48.9, 99], 1, ["123", 123], []]
    for p, v in zip(points, values):
        if (isinstance(v, (int, float)) or all(isinstance(list_item, (int, float)) for list_item in v)) \
                and check_point_is_tuple(p):
            history1.put(p, v)
        elif not (isinstance(v, (int, float)) or all(isinstance(list_item, (int, float)) for list_item in v)):
            with pytest.raises(TypeError,
                               message='point: %s ; VALUE: %s, VALUE is not INT or FLOAT' % (str(p), str(v))):
                history1.put(p, v)
        elif not check_point_is_tuple(p):
            with pytest.raises(TypeError,
                               message='POINT: %s ; value: %s, POINT is not a TUPLE or tuple item is not INT'
                                       % (str(p), str(v))):
                history1.put(p, v)

    for index, point_value in enumerate(points):
        values[index] = [values[index]]
        if (isinstance(values[index][0], (int, float))
                or all(isinstance(list_item, (int, float)) for list_item in values[index][0])) \
                and check_point_is_tuple(point_value):
            assert history1.history[str(point_value)] == values[index]

        else:
            with pytest.raises(KeyError, message='point: %s ; value: %s' %(str(point_value), str(values[index]))):
                history1.history[str(point_value)]


def test_dump(tmpdir):
    history_my = History()
    points = [(2900, 32), (3000, 48), (3000, 32), (2900, 30), (2900, 16), (2900, 30)]
    values = [50, 5, [55, 48, 99], 1, [123.98, 123]]
    for p, v in zip(points, values):
        history_my.put(p, v)
    file_path = tmpdir.join('testfile.txt')
    history_my.dump(file_path)
    assert history_my.dump(file_path) is True
    assert file_path.read() == "(2900, 32)(3000, 48)(3000, 32)(2900, 30)(2900, 16)"
