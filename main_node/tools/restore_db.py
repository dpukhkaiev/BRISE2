import bson
import os
from tools.mongo_dao import MongoDB


class RestoreDB:
    def __init__(self):
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

    def restore(self):
        if self.database.get_last_record("Configuration") is None:
            for c in self.collections:
                with open("Resources/tests/db/" + c + ".bson", "rb+") as f:
                    self.database.write_many_records(c, bson.decode_all(f.read()))

    def cleanup(self):
        self.database.cleanup_database()
