import bson
import os
from tools.mongo_dao import MongoDB
from tools.restore_db import RestoreDB


class TestDB:
    def initialize(self):
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))
        self.collections = ["Configuration",
                            "Experiment_description",
                            "Experiment_state",
                            "Parameter_control_info",
                            "Search_space", "Task",
                            "Transfer_learning_info"]
        if self.database.get_last_record("Configuration") is None:
            rdb = RestoreDB()
            rdb.restore()

    def test_0(self):
        self.initialize()
        assert len(self.database.get_all_records("Configuration")) > 0
