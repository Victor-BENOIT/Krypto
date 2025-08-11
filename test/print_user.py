from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"  # adapte selon ta config Docker / host
client = MongoClient(MONGO_URI)
db = client.krypto

for user in db.users.find():
    print(user)
