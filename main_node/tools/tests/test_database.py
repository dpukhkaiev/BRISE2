import os
import pickle
from collections import OrderedDict
from typing import Tuple

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from core_entities.search_space import get_search_space_record
from tools.initial_config import load_experiment_setup
from tools.mongo_dao import MongoDB

database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))
experiment_description_file = "./Resources/EnergyExperiment/EnergyExperiment.json"


class TestDatabase:
    # this test set is aimed to cover the functionality of database record formatting (by core entities)
    # and the 'mongo_dao' write and read functionality
    # The Mock database 'mongo_db_mock.py' is used.

    # The common structure of all tests is:
    #   1. Create the BRISE 'real' entity
    #   2. Format the database record for this entity
    #   3. Write this record to the database
    #   4. Read the record from the database and compare with the fields of the 'real' entity

    def test_0_write_exp_description_record(self):
        # Test #0. Format and write Experiment description (ED) record to the database
        # Expected result: record can be read from the database and contains all required ED fields. The Experiment id matches
        experiment, _ = self.initialize_experiment()
        database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        written_record = database.get_all_records("Experiment_description")[-1]
        assert experiment.unique_id == written_record["Exp_unique_ID"]
        assert experiment.ed_id == written_record["Exp_ID"]
        assert experiment.description["Context"] == written_record["Context"]
        assert experiment.description["ConfigurationSelection"] == written_record["ConfigurationSelection"]
        assert experiment.description["RepetitionManager"] == written_record["RepetitionManager"]
        assert experiment.description["StopCondition"] == written_record["StopCondition"]

    def test_1_write_exp_state_record(self):
        # Test #1. Format and write Experiment state (ES) record to the database
        # Expected result: record can be read from the database and contains all required ES fields. The Experiment id matches
        experiment, _ = self.initialize_experiment()
        c1 = Configuration(OrderedDict({"frequency": 2900.0, "threads": 32}), Configuration.Type.DEFAULT, experiment.unique_id)
        experiment.default_configuration = c1
        database.write_one_record("Experiment_state", experiment.get_experiment_state_record())
        written_record = database.get_all_records("Experiment_state")[-1]
        assert experiment.unique_id == written_record["Exp_unique_ID"]
        assert experiment.get_number_of_measured_configurations() == written_record["Number_of_measured_configs"]
        assert experiment.get_bad_configuration_number() == written_record["Number_of_bad_configs"]
        assert experiment.get_current_solution().get_configuration_record() == written_record["Current_solution"]
        assert experiment.get_model_state() == written_record["is_model_valid"]

    def test_2_write_search_space_record(self):
        # Test #2. Format and write Search space (SS) record to the database
        # Expected result: record can be read from the database and contains all required SS fields.
        # The Experiment id matches. The id of the default configuration matches that one from Experiment
        experiment, search_space = self.initialize_experiment()
        database.write_one_record(
            "Search_space", get_search_space_record(experiment.search_space, experiment.unique_id)
        )
        written_record = database.get_all_records("Search_space")[-1]
        assert written_record["Exp_unique_ID"] == experiment.unique_id
        assert written_record["SearchspaceObject"] == pickle.dumps(search_space)
        assert written_record["Search_space_size"] == search_space.size

    def test_3_write_measured_configurations_records(self):
        # Test #3. Format and write multiple Configuration records to the database
        # Expected result: records can be read from the database.
        # They belong to the expected experiment and contain expected configuration IDs
        experiment, _ = self.initialize_experiment()
        c1 = Configuration(OrderedDict({"frequency": 2900.0, "threads": 32}), Configuration.Type.DEFAULT, experiment.unique_id)
        c2 = Configuration(OrderedDict({"frequency": 2200.0, "threads": 8}), Configuration.Type.FROM_SELECTOR, experiment.unique_id)
        experiment.measured_configurations.append(c1)
        experiment.measured_configurations.append(c2)
        records = []
        for config in experiment.measured_configurations:
            records.append(config.get_configuration_record())
        database.write_many_records("Configuration", records)
        written_records = database.get_all_records("Configuration")
        configuration_ids = []
        experiment_ids = []
        for record in written_records:
            configuration_ids.append(record["Configuration_ID"])
            experiment_ids.append(record["Exp_unique_ID"])
        assert c1.unique_id in configuration_ids
        assert c2.unique_id in configuration_ids
        assert experiment.unique_id in experiment_ids

    def test_4_write_task_record(self):
        # Test #4. Format and write Task record to the database
        # Expected result: record can be read from the database.
        # Task belongs to the expected configuration and has expected task ID
        c1 = Configuration(OrderedDict({"frequency": "dummy", "threads": "dummy"}), Configuration.Type.DEFAULT, "DummyID")
        task = {'task id': 'id', 'worker': 'worker', 'result': {'energy': 0.9}, 'ResultValidityCheckMark': 'OK'}
        c1.add_task(task)
        database.write_one_record("Task", c1.get_task_record(task))
        written_record = database.get_all_records("Task")[-1]
        assert c1.unique_id == written_record["Configuration_ID"]
        assert task['task id'] == written_record["Task_ID"]
        assert task == written_record["Task"]

    @staticmethod
    def initialize_experiment() -> Tuple[Experiment, SearchSpace]:
        experiment_description, search_space = load_experiment_setup(experiment_description_file)
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, search_space
