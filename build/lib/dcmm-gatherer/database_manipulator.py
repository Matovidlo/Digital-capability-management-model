import numpy
from pymongo import MongoClient
from API_adapter import Request


class DatabaseManipulator(Request):
    def __init__(self, urls, username='root', password="anypass"):
        self.client = MongoClient(username=username, password=password)
        self._loaded_data = None
        print(self.client.list_database_names())
        # Create new DCMM Database
        db = self.client["DCMMDatabase"]
        # Create collections based on the urls
        self.collections = []
        for key in urls.keys():
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
                    data.append(found)
        return cursors, data

    def write_data(self, data, collection_name):
        concrete_collection = [filter_collection
                               for filter_collection in self.collections
                               if filter_collection.name == collection_name][0]
        is_nested = False
        for index, nested_value in enumerate(data):
            if isinstance(nested_value, list):
                is_nested = True
                concrete_collection.insert_many(nested_value)
            # Replace all dots to hyphen
            replace = []
            for key, value in nested_value.items():
                new_key = key.replace('.', '-')
                replace.append((new_key, key))
            for value in replace:
                nested_value[value[0]] = nested_value.pop(value[1])
        # for key, value in data:
        if not is_nested:
            concrete_collection.insert_many(data)

    def update_data(self, data, model_data, collection_name):
        concrete_collection = [filter_collection
                               for filter_collection in self.collections
                               if filter_collection.name == collection_name][0]
        for prediction, key in zip(data, model_data):
            updated = concrete_collection.update_one({'description': key},
                                                     {'$set': {'preditcted': str(prediction)}})
            if not updated:
                print("Could not update {}".format(key))
                break

    def __str__(self):
        return "DatabaseManipulator class"
