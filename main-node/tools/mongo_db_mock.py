from typing import Mapping
import uuid


class MongoDB_mock():
    def __init__(self):
        self.collections_names = ["Experiment_description", "Search_space", "Measured_configurations", "Experiment_state", "Tasks"]
        self.collections = {}
        for collection in self.collections_names:
            self.init_collection(collection)

    def init_collection(self, collection_name: str):
        collection = Collection(collection_name)
        self.collections[collection_name] = collection


class Collection():
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.rows = []

    def insert_one(self, record: Mapping):
        self.rows.append(record)
        return Insertion(str(uuid.uuid4()))

    def insert_many(self, records: list):
        ids = []
        for rec in records:
            self.rows.append(rec)
            ids.append(str(uuid.uuid4()))
        return MultipleInsertion(ids)

    def find(self):
        return self.rows

class Insertion():
    def __init__(self, id: str):
        self.inserted_id = id

class MultipleInsertion():
    def __init__(self, ids: list):
        self.inserted_ids = ids
    