from pymongo import MongoClient
from API_adapter import Request


class DatabaseManipulator(Request):
    def __init__(self, urls):
        self.client = MongoClient(username="root", password="extrastrongpasswd")
        self._loaded_data = None
        print(self.client.list_database_names())
        # Create new DCMM Database
        db = self.client["DCMMDatabase"]
        # Create collections based on the urls
        self.collections = []
        for key in urls.keys():
            self.collections.append(db[key])

    def send_requests(self) -> tuple:
        return super(DatabaseManipulator, self).send_requests()

    def get_data(self, concrete_data=None, collection_name=None, date=None):
        cursors = []
        data = None
        if collection_name:
            concrete_collection = [filter_collection
                                   for filter_collection in self.collections
                                   if
                                   filter_collection.name == collection_name][0]
            cursors.append(concrete_collection.find())
            for found in cursors[0]:
                data = found
                print(found)
        else:
            for collection in self.collections:
                cursors.append(collection.find())
                for found in cursors[-1]:
                    data = found
                    print(found)
        return cursors, data

    def write_data(self, data, collection_name):
        concrete_collection = [filter_collection
                               for filter_collection in self.collections
                               if filter_collection.name == collection_name][0]
        is_nested = False
        for nested_value in data:
            if isinstance(nested_value, list):
                is_nested = True
                concrete_collection.insert_many(nested_value)
        # for key, value in data:
        if not is_nested:
            concrete_collection.insert_many(data)

    def __str__(self):
        return "DatabaseManipulator class"