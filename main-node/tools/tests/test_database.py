import pytest
import os

from tools.mongo_dao import MongoDB
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from tools.initial_config import load_experiment_setup

os.environ["TEST_MODE"] = 'UNIT_TEST'
database = MongoDB("test", 0, "test", "user", "pass")
experiment_description_file = "./Resources/EnergyExperiment.json"

class TestDatabase:
    # this test set is aimed to cover the functionality of database record formatting (by core entities) 
    # and the 'mongo_dao' write and read functionality
    # The Mock database 'mongo_db_mock.py' is used.

    # The common strtucture of all tests is:
    #   1. Create the BRISE 'real' entity
    #   2. Format the database record for this entity
    #   3. Write this record to the database
    #   4. Read the record from the database and compare with the fileds of the 'real' entity

    def test_0_write_exp_description_record(self):
        # Test #0. Format and write Experiment description (ED) record to the database
        # Expected result: record can be read from the database and contains all required ED fields. The Experiment id matches
        experiment, _ = self.initialize_exeriment()
        database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        written_record = database.get_all_records("Experiment_description")[0]
        assert experiment.unique_id == written_record["Exp_unique_ID"]
        assert experiment.ed_id == written_record["Exp_ID"]
        assert experiment.description["General"]["isMinimizationExperiment"] == written_record["isMinimizationExperiment"]
        assert experiment.description["DomainDescription"] == written_record["DomainDescription"]
        assert experiment.description["TaskConfiguration"] == written_record["TaskConfiguration"]
        assert experiment.description["SelectionAlgorithm"] == written_record["SelectionAlgorithm"]
        assert experiment.description["OutliersDetection"] == written_record["OutliersDetection"]
        assert experiment.description["Repeater"] == written_record["Repeater"]
        assert experiment.description["ModelConfiguration"] == written_record["ModelConfiguration"]
        assert experiment.description["StopCondition"] == written_record["StopCondition"]
        assert experiment.description["StopConditionTriggerLogic"] == written_record["StopConditionTriggerLogic"]

    def test_1_write_exp_state_record(self):
        # Test #1. Format and write Experiment state (ES) record to the database
        # Expected result: record can be read from the database and contains all required ES fields. The Experiment id matches
        experiment, _ = self.initialize_exeriment()
        c1 = Configuration([2900.0, 32], Configuration.Type.DEFAULT)
        experiment.measured_configurations.append(c1)
        database.write_one_record("Experiment_state", experiment.get_experiment_state_record())
        written_record = database.get_all_records("Experiment_state")[0]
        assert experiment.unique_id == written_record["Exp_unique_ID"]
        assert experiment.get_number_of_measured_configurations() == written_record["Number_of_measured_configs"]
        assert experiment.get_bad_configuration_number() == written_record["Number_of_bad_configs"]
        assert experiment.get_current_solution().get_configuration_record(experiment.unique_id) == written_record["Current_solution"]
        assert experiment.get_model_state() == written_record["is_model_valid"]

    def test_2_write_search_space_record(self):
        # Test #2. Format and write Search space (SS) record to the database
        # Expected result: record can be read from the database and contains all required SS fields. 
        # The Experiment id matches. The id of the default configuration matches that one from Experiment
        experiment, search_space = self.initialize_exeriment()
        database.write_one_record("Search_space", experiment.search_space.get_search_space_record(experiment.unique_id))
        written_record = database.get_all_records("Search_space")[0]
        assert written_record["Exp_unique_ID"] == experiment.unique_id
        assert written_record["Default_configuration"] == experiment.search_space.get_default_configuration()
        assert written_record["Search_space_size"] == search_space.get_search_space_size()

    def test_3_write_measured_configurations_records(self):
        # Test #3. Format and write multiple Configuration records to the database
        # Expected result: records can be read from the database. 
        # They belong to the expected experiment and contain expected configuration IDs
        experiment, _ = self.initialize_exeriment()
        c1 = Configuration([2900.0, 32], Configuration.Type.DEFAULT)
        c2 = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
        experiment.measured_configurations.append(c1)
        experiment.measured_configurations.append(c2)
        records = []
        for config in experiment.measured_configurations:
            records.append(config.get_configuration_record(experiment.unique_id))
        database.write_many_records("Measured_configurations", records)
        written_records = database.get_all_records("Measured_configurations")
        assert c1.unique_id in [written_records[0]["Configuration_ID"], written_records[1]["Configuration_ID"]]
        assert c2.unique_id in [written_records[0]["Configuration_ID"], written_records[1]["Configuration_ID"]]
        assert experiment.unique_id == written_records[0]["Exp_unique_ID"] == written_records[1]["Exp_unique_ID"]

    def test_4_write_task_record(self):
        # Test #4. Format and write Task record to the database
        # Expected result: record can be read from the database. 
        # Task belongs to the expected configuration and has expected task ID
        c1 = Configuration(["dummy"], Configuration.Type.DEFAULT)
        task = {'task id': 'id', 'worker': 'worker', 'result': {'PREC_AT_99_REC': 0.9}, 'ResultValidityCheckMark': 'OK'}
        c1.add_tasks(task)
        database.write_one_record("Tasks", c1.get_task_record(task))
        written_record = database.get_all_records("Tasks")[0]
        assert c1.unique_id == written_record["Configuration_ID"]
        assert task['task id'] == written_record["Task_ID"]
        assert task == written_record["Task"]

    def initialize_exeriment(self):
        experiment_description, search_space = load_experiment_setup(experiment_description_file)
        experiment = Experiment(experiment_description, search_space)
        return experiment, search_space

