import logging
import urllib.parse
from typing import Mapping, Union

import pymongo
from worker_tools.singleton import Singleton


class MongoDB(metaclass=Singleton):
    '''
    This class plays a role of the Data Access Object (DAO) for MongoDB.
    It contains main CRUD operations (Create, Read, Update and Delete), used by BRISE to operate with a database
    '''
    def __init__(self, mongo_host: str, mongo_port: int, database_name: str, user: str, passwd: str):
        username = urllib.parse.quote_plus(user)
        password = urllib.parse.quote_plus(passwd)
        parameters = dict({
            "host": mongo_host + ":" + str(mongo_port),
            "username": username,
            "password": password
        })

        if "localhost" not in mongo_host and "127.0.0.1" not in mongo_host:
            # Running non-locally deployed MongoDB instance, therefore, need to authenticate.
            parameters["authSource"] = database_name
        self.client = pymongo.MongoClient(**parameters)
        self.database = self.client[database_name]
        self.logger = logging.getLogger(__name__)

    def get_last_record_by_experiment_id(self, collection_name: str, exp_id: str) -> Union[Mapping, None]:
        collection = self.database[collection_name]
        records = collection.find({"Exp_unique_ID": exp_id})
        if records.count() > 0:
            for record in records.skip(records.count() - 1):
                return dict(record)
        else:
            return None

    def update_record(self, collection_name: str, query: Mapping, new_val: Mapping) -> None:
        collection = self.database[collection_name]
        new_values = {"$set": new_val}
        collection.update_one(query, new_values)
