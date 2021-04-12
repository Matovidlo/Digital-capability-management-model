import os
import pymongo
import bson
import uuid

client = pymongo.MongoClient(username=os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin"),
                             password=os.getenv("MONGO_INITDB_ROOT_PASSWORD", "extrastrongpass"))
db = client[os.getenv("DATABASE", "DCMMDatabase")]
# Create collections based on the urls
model = db['model_path']
# Drop models and Github repositories
if db['model_path'].count() != 0:
    db['model_path'].drop()
if db['Github'].count() != 0:
    db['Github'].drop()
# serialization
unique_id = uuid.uuid4()
with open("/tmp/model/model.sav", "rb") as f:
    bin_object = f.read()
    model.insert_one({
        "model": unique_id,
        "binary_field": bson.Binary(bin_object),
    })
with open("/tmp/model/vectorizer.sav", "rb") as f:
    bin_object = f.read()
    model.insert_one({
        "model": unique_id,
        "binary_field": bson.Binary(bin_object),
    })
with open("/tmp/model/tf_transformer.sav", "rb") as f:
    bin_object = f.read()
    model.insert_one({
        "model": unique_id,
        "binary_field": bson.Binary(bin_object),
    })
print("Succesfully done")
# deserialization
# pickle.loads(record["binary_field"])
