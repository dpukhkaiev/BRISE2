import os
from typing import List
from bson import BSON
from tools.mongo_dao import MongoDB


def dump(database: MongoDB, collections: List):
    for c in collections:
        with open("Resources/tests/db/" + c + ".bson", "wb+") as f:
            for e in database.get_all_records(c):
                f.write(BSON.encode(e))


if __name__ == "__main__":
    database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                       os.getenv("BRISE_DATABASE_PORT"),
                       os.getenv("BRISE_DATABASE_NAME"),
                       os.getenv("BRISE_DATABASE_USER"),
                       os.getenv("BRISE_DATABASE_PASS"))
    collections = ["Configuration",
                   "Experiment_description",
                   "Experiment_state",
                   "Parameter_control_info",
                   "Search_space", "Task",
                   "Transfer_learning_info"]
    dump(database, collections)
