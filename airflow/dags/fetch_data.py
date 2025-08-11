from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from pymongo import MongoClient
import os

def fetch_binance_trades():
    # Appel API Binance (clé API à gérer)
    # Ici on simule les données
    trades = [{"symbol": "BTCUSDT", "qty": 0.01, "price": 30000, "ts": datetime.now()}]
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"))
    db = client.krypto
    db.transactions.insert_many(trades)

default_args = {
    "owner": "krypto",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    "fetch_crypto_data",
    default_args=default_args,
    description="Fetch Binance & Bittensor data",
    schedule_interval="0 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False
) as dag:

    t1 = PythonOperator(
        task_id="fetch_binance_trades",
        python_callable=fetch_binance_trades
    )
