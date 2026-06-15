import pytest

from reconfiguration.reconfiguration_executor import ReconfigurationExecutor
from reconfiguration.effector import Effector

class TestReconfigurationExecutor:

    @pytest.fixture(scope="function")
    def executor(self):
        return ReconfigurationExecutor()

    def test_change_identifiers(self, executor:ReconfigurationExecutor):
        """Test that identifiers work as intended"""
        class TestClass1:
            def __init__(self):
                self._init_test_variability_point({})

            @Effector.effector("test-vp")
            def _init_test_variability_point(self, description):
                self.value = description

        class TestClass2:
            def __init__(self):
                self.some_id = "test-id"
                self._init_test_variability_point({})

            @Effector.effector("test-vp", identifiers="some_id")
            def _init_test_variability_point(self, description):
                self.value = description

        class TestClass3:
            def __init__(self):
                self.some_ids = ["test-id", "test-id-2"]
                self._init_test_variability_point({})

            @Effector.effector("test-vp", identifiers="some_ids")
            def _init_test_variability_point(self, description):
                self.value = description

        test_class_1 = TestClass1()
        test_class_2 = TestClass2()
        test_class_3 = TestClass3()

        classes = [test_class_1, test_class_2, test_class_3]

        assert len(Effector.get_all()) == 3

        executor.update_effectors()
        assert len(executor.effectors) == 1
        assert len(executor.effectors["test-vp"]) == 3
        
        # Change without the identifer -> change all values
        new_val = {"x": 10}
        executor.change("test-vp", new_val, new_val, None)

        for c in classes:
            assert c.value == new_val

        # Change with test-id one -> only class 2 should be effected
        new_val = {"x": 12}
        executor.change("test-vp", new_val, new_val, ["test-id"])

        assert test_class_1.value != new_val
        assert test_class_2.value == new_val
        assert test_class_3.value != new_val

        # Change with test-id and test-id-2 -> only class 3 should be effected
        new_val = {"x": 15}
        executor.change("test-vp", new_val, new_val, ["test-id", "test-id-2"])

        assert test_class_1.value != new_val
        assert test_class_2.value != new_val
        assert test_class_3.value == new_val
