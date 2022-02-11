from pymongo import MongoClient
import sys
import json
sys.path.append("..")


with open("keys_mongodb.json", "r") as f:
    KEYS = json.load(f)
CLIENT = MongoClient(
    f"mongodb+srv://{KEYS['username']}:{KEYS['password']}@cluster0.eldr7.mongodb.net/Leda?ssl=true&retryWrites=true&w=majority")
DB = CLIENT.Leda
LOOKUP_TABLE_PATH = "../data/lookup_tables"


def update_lookup_table(db, collection, feature):
    values = ",\n".join(set([doc[feature] for doc in db[collection].find({})]))
    with open(f"{LOOKUP_TABLE_PATH}/{feature}.txt", "w") as f:
        f.write(values)


#update_lookup_table("sector", DB)
