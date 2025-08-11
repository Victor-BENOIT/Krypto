from fastapi import FastAPI
from pymongo import MongoClient
import os

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
client = MongoClient(MONGO_URI)
db = client.krypto

@app.get("/portfolio")
def get_portfolio():
    data = list(db.transactions.find({}, {"_id": 0}))
    return {"transactions": data}
