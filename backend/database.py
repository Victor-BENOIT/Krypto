import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client_mongo = MongoClient("mongodb://localhost:27017")
db = client_mongo.krypto

def ensure_collection_exists(collection_name):
    """Crée la collection si elle n'existe pas déjà."""
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        print(f"✅ Collection '{collection_name}' créée.")
    else:
        print(f"ℹ️ Collection '{collection_name}' déjà existante.")