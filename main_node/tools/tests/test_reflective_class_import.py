import pytest
from tools.reflective_class_import import reflective_class_import


class TestReflectiveClassImport:
    # this test set is aimed to cover the functionality of the 'reflective_class_import' tool

    def test_0_import_by_full_name(self):
        # Test #0. Import class by its full name
        # Expected result: class is successfully imported
        expected_result = "SobolSequence"
        actual_result = reflective_class_import(class_name="SobolSequence", folder_path="configuration_selection/sampling")
        assert actual_result.__name__ == expected_result

    def test_1_import_by_partial_name(self):
        # Test #1. Import class by its partial name
        # Expected result: class is successfully imported
        expected_result = "SobolSequence"
        actual_result = reflective_class_import(class_name="Sobol", folder_path="configuration_selection/sampling")
        assert actual_result.__name__ == expected_result

    def test_2_import_by_part_of_name(self):
        # Test #2. Import class by an excessive name (redundant symbols are present)
        # Expected result: class is successfully imported
        expected_result = "SobolSequence"
        actual_result = reflective_class_import(class_name="SobolSequence123", folder_path="configuration_selection/sampling")
        assert actual_result.__name__ == expected_result

    def test_3_contraversial_import_by_of_name(self):
        # Test #3. Import class by a contraversial name (contains names of more than 1 class)
        # Expected result: class with the closest name is successfully imported
        expected_result = "MersenneTwister"
        actual_result = reflective_class_import(class_name="SobolSequenceMersenneTwister", folder_path="configuration_selection/sampling")
        assert actual_result.__name__ == expected_result

    def test_4_import_by_lower_case_name(self):
        # Test #4. Import class by its lower case name
        # Expected result: class is successfully imported
        expected_result = "SobolSequence"
        actual_result = reflective_class_import(class_name="sobolsequence", folder_path="configuration_selection/sampling")
        assert actual_result.__name__ == expected_result

    def test_5_import_by_invalid_name(self):
        # Test #5. Try to import class by non-existing name
        # Expected result: class is not imported, error is raised
        expected_result = "does not contain any classes!"
        with pytest.raises(NameError) as excinfo:
            reflective_class_import(class_name="InvalidName", folder_path="configuration_selection/sampling")
        assert expected_result in str(excinfo.value)

    def test_6_import_by_empty_name(self):
        # Test #6. Try to import class by an empty name
        # Expected result: class is not imported, error is raised
        expected_result = "class_name parameter should be non-empty string"
        with pytest.raises(TypeError) as excinfo:
            reflective_class_import(class_name="", folder_path="configuration_selection/sampling")
        assert expected_result in str(excinfo.value)

    def test_7_import_from_empty_directory(self):
        # Test #7. Try to import class from an empty directory
        # Expected result: class is not imported, error is raised
        import os

        # create an empty folder for test
        os.makedirs('./test_folder/', exist_ok=True)
        expected_result = "Specified directory 'test_folder' is empty."
        with pytest.raises(NameError) as excinfo:
            reflective_class_import(class_name="SomeClass", folder_path="test_folder")
        assert expected_result in str(excinfo.value)
        # cleanup
        if os.path.exists("./test_folder"):
            os.rmdir("./test_folder")

    def test_9_import_if_multiple_choices(self, caplog):
        # Test #9. Try to import class if many classes meet the request
        # Expected result: class with the most similar name is imported, warning is emmited
        # TODO: check expected behavior: alphabet order is used if all names are the same
        # only 1 class is being found in module, if classes are in different files!
        import logging
        caplog.set_level(logging.WARNING)
        expected_result = "more than one Class provided"
        expected_class = "API"
        actual_result = reflective_class_import(class_name="API", folder_path="tools")
        for record in caplog.records:
            assert record.levelname == "WARNING"
            assert expected_result in str(record)
        assert actual_result.__name__ == expected_class

    def test_10_import_by_non_str_name(self):
        # Test #10. Try to import class by a non-string name
        # Expected result: class is not imported, error is raised
        expected_result = "class_name parameter should be non-empty string"
        with pytest.raises(TypeError) as excinfo:
            reflective_class_import(class_name=None, folder_path="configuration_selection/sampling")
        assert expected_result in str(excinfo.value)
