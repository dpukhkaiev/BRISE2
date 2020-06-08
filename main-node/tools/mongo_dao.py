import pymongo
import urllib.parse
import logging
import os

from tools.singleton import Singleton
from typing import Mapping, Union


class MongoDB(metaclass=Singleton):
    '''
    This class plays a role of the Data Access Object (DAO) for MongoDB.
    It contains main CRUD operations (Create, Read, Update and Delete), used by BRISE to operate with a database
    '''
    def __init__(self, mongo_host: str, mongo_port: int, database_name: str, user: str, passwd: str):
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            username = urllib.parse.quote_plus(user)
            password = urllib.parse.quote_plus(passwd)
            self.client = pymongo.MongoClient(mongo_host + ":" + str(mongo_port), username=username, password=password, authSource=database_name)
            self.database = self.client[database_name]
        else:
            # if test mode - initialize connection to a database mock
            from tools.mongo_db_mock import MongoDB_mock
            mock_database = MongoDB_mock()
            self.database = mock_database.collections

        self.logger = logging.getLogger(__name__)

    def write_one_record(self, collection_name: str, record: Mapping) -> None:
        collection = self.database[collection_name]
        x = collection.insert_one(record)
        self.logger.debug("Written to mongo. Id: " + str(x.inserted_id))

    def write_many_records(self, collection_name: str, records: list) -> None:
        collection = self.database[collection_name]
        x = collection.insert_many(records)
        self.logger.debug("Written to mongo. Id: " + str(x.inserted_ids))

    def get_all_records(self, collection_name: str) -> list:
        result = []
        collection = self.database[collection_name]
        for record in collection.find():
            result.append(dict(record))
        return result

    def get_last_record(self, collection_name: str) -> Union[Mapping, None]:
        collection = self.database[collection_name]
        if collection.count() > 0:
            for record in collection.find().skip(collection.count() - 1):
                return dict(record)
        else:
            self.logger.warning("Unable to get last record from an empty collection")
            return None

    def get_records_by_experiment_id(self, collection_name: str, exp_id: str) -> list:
        result = []
        collection = self.database[collection_name]
        for record in collection.find({"Exp_unique_ID": exp_id}):
            result.append(dict(record))
        return result

    def get_last_record_by_experiment_id(self, collection_name: str, exp_id: str) -> Union[Mapping, None]:
        collection = self.database[collection_name]
        records = collection.find({"Exp_unique_ID": exp_id})
        if records.count() > 0:
            for record in records.skip(records.count() - 1):
                return dict(record)
        else:
            self.logger.warning("Unable to retrieve record by requested Experiment ID")
            return None

    def update_record(self, collection_name: str, query: Mapping, new_val: Mapping) -> None:
        collection = self.database[collection_name]
        new_values = {"$set": new_val}
        collection.update_one(query, new_values)
