from datetime import datetime
import numpy
from pymongo import MongoClient
from API_adapter import Request
from threading import Lock, Thread


class SingletonMeta(type, Request):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class DatabaseManipulator(metaclass=SingletonMeta):
    def __init__(self, urls, username='root', password="anypass"):
        self.client = MongoClient(username=username, password=password)
        self._loaded_data = None
        # Create new DCMM Database
        db = self.client["DCMMDatabase"]
        self.urls = urls
        # Create collections based on the urls
        self.collections = []
        self.create_collections(db)

    def create_collections(self, db):
        for key in self.urls.keys():
            self.collections.append(db[key])
        self._cursor = db['model_path'].find()

    @property
    def model_cursor(self):
        return self._cursor

    def send_requests(self) -> tuple:
        return super(DatabaseManipulator, self).send_requests()

    def get_data(self, concrete_data=None, collection_name=None, date=None):
        cursors = []
        data = []
        if collection_name:
            concrete_collection = [filter_collection
                                   for filter_collection in self.collections
                                   if
                                   filter_collection.name == collection_name][0]
            cursors.append(concrete_collection.find())
            for found in cursors[0]:
                data.append(found)
        else:
            for collection in self.collections:
                cursors.append(collection.find())
                for found in cursors[-1]:
                    if date and 'created_at' in found:
                        created_date = datetime.strptime(found['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                        if created_date >= date:
                            data.append(found)
                    elif not date:
                        data.append(found)
        return cursors, data

    def write_data(self, data, collection_name):
        concrete_collection = [filter_collection
                               for filter_collection in self.collections
                               if filter_collection.name == collection_name][0]
        is_nested = False
        for index, nested_value in enumerate(data):
            if isinstance(nested_value, (list, tuple)):
                is_nested = True
                concrete_collection.insert_many(nested_value)
                continue
            # Replace all dots to hyphen
            replace = []
            for key, value in nested_value.items():
                new_key = key.replace('.', '-')
                replace.append((new_key, key))
            for value in replace:
                nested_value[value[0]] = nested_value.pop(value[1])
        # for key, value in data:
        if not is_nested and data:
            concrete_collection.insert_many(data)

    def update_data(self, data, model_data, collection_name, set_key=None):
        concrete_collection = [filter_collection
                               for filter_collection in self.collections
                               if filter_collection.name == collection_name][0]
        for prediction, key in zip(data, model_data):
            if not set_key:
                updated = concrete_collection.update_one({'description': key},
                                                         {'$set': {'predicted': str(prediction)}})
            else :
                updated = concrete_collection.update_one({'description': key},
                                                         {'$set': {
                                                             set_key: str(
                                                                 prediction)}})
            if not updated:
                print("Could not update {}".format(key))
                break

    def __str__(self):
        return "DatabaseManipulator class"
