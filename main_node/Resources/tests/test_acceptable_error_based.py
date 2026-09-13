from repeater.acceptable_error_based import AcceptableErrorBasedType


class FakeDatabase:
    def get_last_record_by_experiment_id(self, collection_name, experiment_id):
        return {"Current_solution": {"Results": {"obj_1": 100.0, "obj_2": 100.0}}}


class FakeConfiguration:
    results = {"obj_1": 100.0, "obj_2": 100.0}

    def get_tasks(self):
        return [object(), object(), object()]

    def get_standard_deviation(self):
        return [0.0, 0.0]


def test_scalar_base_acceptable_error_is_used_for_each_objective():
    repeater = AcceptableErrorBasedType.__new__(AcceptableErrorBasedType)
    repeater.objectives = {
        "obj_1": {"Minimization": True},
        "obj_2": {"Minimization": True},
    }
    repeater.objectives_minimization = [True, True]
    repeater.min_tasks_per_configuration = 2
    repeater.max_tasks_per_configuration = 7
    repeater.base_acceptable_errors = 5.0
    repeater.confidence_levels = 0.95
    repeater.is_experiment_aware = False
    repeater.experiment_id = "test"
    repeater.database = FakeDatabase()

    assert repeater.evaluate(FakeConfiguration()) == 0
