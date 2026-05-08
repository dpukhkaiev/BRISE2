import pytest

from reconfiguration.effector import Effector

class TestEffector:

    @pytest.fixture(scope="function")
    def single_vp_setup(self):
        class TestClass:
            def __init__(self):
                self._init_test_variability_point({})

            @Effector.effector("test-vp")
            def _init_test_variability_point(self, description):
                self.value = description
        return TestClass()
    
    @pytest.fixture(autouse=True)
    def clear_effectors(self):
        Effector.clear_all()

    def test_decorator(self):
        """Test that the decorator registers a new variability point and does not create duplicate instances"""

        class TestClass:
            def __init__(self):
                self._init_test_variability_point({})
                self._init_test_variability_point({}) # Call init method twice!

            @Effector.effector("test-vp")
            def _init_test_variability_point(self, description):
                self.value = description

        test_class = TestClass()

        assert len(Effector.get_all()) == 1
        effector = Effector.get_all()[0]
        assert effector.vp == "test-vp"

        test_class_2 = TestClass()
        assert len(Effector.get_all()) == 2

    def test_decorator_arguments(self):
        """Test that the arguments of the decorator work"""

        # No special arguments
        class TestClass1:
            def __init__(self):
                self._init_test_variability_point({})

            @Effector.effector("test-vp")
            def _init_test_variability_point(self, description):
                self.value = description

        TestClass1()
        assert len(Effector.get_all()) == 1

        effector = Effector.get_all()[0]
        assert effector.full_description is False
        assert effector.identifiers == []

        Effector.clear_all()

        # Add single identifier -> make list out of it
        class TestClass2:
            def __init__(self):
                self.some_id = "test-id"
                self._init_test_variability_point({})

            @Effector.effector("test-vp", identifiers="some_id")
            def _init_test_variability_point(self, description):
                self.value = description

        TestClass2()
        assert len(Effector.get_all()) == 1

        effector = Effector.get_all()[0]
        assert len(effector.identifiers) == 1
        assert effector.identifiers[0] == "test-id"

        Effector.clear_all()

        # Add multiple identfiers
        class TestClass3:
            def __init__(self):
                self.some_ids = ["id-1", "id-2"]
                self._init_test_variability_point({})

            @Effector.effector("test-vp", identifiers="some_ids")
            def _init_test_variability_point(self, description):
                self.value = description

        TestClass3()
        assert len(Effector.get_all()) == 1

        effector = Effector.get_all()[0]
        assert effector.full_description is False
        assert len(effector.identifiers) == 2
        assert all(i in ["id-1", "id-2"] for i in effector.identifiers)

    def test_change(self, single_vp_setup):
        """Test that the change method works correctly"""
        test_class = single_vp_setup

        assert test_class.value == {}

        new_value = {"txt": "Hallo Welt"}
        self.change_vp("test-vp", new_value)

        assert test_class.value == new_value

    def test_nested_effectors(self):
        """Test that nested effectors work and cleanup method removes unused effectors"""
        class SubComp:
            def __init__(self, description):
                self._init_test_variability_point(description)

            @Effector.effector("test-vp-sub")
            def _init_test_variability_point(self, description):
                self.value = description

        class MasterComp:
            def __init__(self):
                self._init_sub_comp({})

            @Effector.effector("test-vp-master")
            def _init_sub_comp(self, description):
                self.sub_comp = SubComp(description)

        master_comp = MasterComp()
        master_holder = [master_comp] # To avoid that the effector is cleaned up

        assert len(Effector.get_all()) == 2
        assert master_comp.sub_comp.value == {}

        # Change Sub component value
        new_desc_sub = {"txt": "From sub"}
        self.change_vp("test-vp-sub", new_desc_sub)

        assert master_comp.sub_comp.value == new_desc_sub

        # Change master component
        new_desc_master = {"txt": "From master"}
        self.change_vp("test-vp-master", new_desc_master)
        assert master_comp.sub_comp.value == new_desc_master

        # One effector of the old sub component is still there but unused
        self._print_effectors()
        assert len(Effector.get_all()) == 3

        # Cleanup
        Effector.cleanup()
        assert len(Effector.get_all()) == 2

        # Check that new effector still works
        new_desc_sub = {"txt": "From sub"}
        self.change_vp("test-vp-sub", new_desc_sub)

        assert master_comp.sub_comp.value == new_desc_sub

    def test_dynamic_identifiers(self):
        """Test that it is possible to register the same VP with differtent identifiers by setting the var right before the registration"""
        class TestClass:
            def __init__(self):
                self._init_test_variability_point({})

            @Effector.effector("test-vp")
            def _init_test_variability_point(self, description):
                self.some_map = {}

                for x in range(3):
                    self.current_sub_id = x # Dynamically change the id that the effector will be registered with
                    self._init_sub_vp({"key": x, "value": x * 2})

            @Effector.effector("test-vp", identifiers="current_sub_id")
            def _init_sub_vp(self, description):
                self.some_map[description["key"]] = description["value"]

        test_class = TestClass()
        assert len(Effector.get_all()) == 4

        # Assert all sub ids are registered
        sub_ids = []
        for e in Effector.get_all():
            if e.identifiers is not None and len(e.identifiers) > 0:
                sub_ids.extend(e.identifiers)

        assert len(sub_ids) == 3
        assert all([x in sub_ids for x in range(3)])

    def test_dynamic_vp_name(self):
        """Test that it is possible to register dynamically named VPs by setting the var right before the registration"""
        class TestClass:
            def __init__(self):
                self.vp_name = "dynamic-vp"
                self._init_test_variability_point({})

            @Effector.effector("ATTR:vp_name")
            def _init_test_variability_point(self, description):
                self.value = description

        test_class = TestClass()
        assert len(Effector.get_all()) == 1
        assert Effector.get_all()[0].vp == "dynamic-vp"

    ### Helper methods ###
    def change_vp(self, vp:str, new_description):
        """Call the change method on a given variability point"""
        for e in Effector.get_all():
            if e.vp != vp:
                continue

            e.change(new_description)

    def _print_effectors(self):
        """For debugging the tests"""
        print([e.vp + " " + str(e.identifiers) for e in Effector.get_all()])

    