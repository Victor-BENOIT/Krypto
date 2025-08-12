from pymongo import MongoClient
from cryptography.fernet import Fernet
from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()


def get_binance_client(username: str, fernet: Fernet) -> Client:
    user = db.users.find_one({"username": username})
    if not user:
        print(f"Utilisateur {username} non trouvé")
        return

    encrypted_api_key = user.get("binance_api_key")
    encrypted_api_secret = user.get("binance_api_secret")
    if not encrypted_api_key or not encrypted_api_secret:
        print("Clés Binance non configurées pour cet utilisateur.")
        return

    try:
        api_key = fernet.decrypt(encrypted_api_key.encode()).decode()
        api_secret = fernet.decrypt(encrypted_api_secret.encode()).decode()
    except Exception as e:
        print("Erreur déchiffrement clés Binance:", e)
        return

    return Client(api_key, api_secret)

def fetch_and_store_balances(username: str, fernet: Fernet, db: MongoClient) -> None:

    try:
        client_binance = get_binance_client(username, fernet)
        account_info = client_binance.get_account()
        balances = account_info.get("balances", [])

        available_assets = []
        loan_debt_assets = []

        for b in balances:
            asset = b["asset"]
            free_amt = float(b["free"])
            locked_amt = float(b["locked"])

            if free_amt == 0 and locked_amt == 0:
                continue

            if asset.startswith("LD"):
                loan_debt_assets.append({
                    "asset": asset[2:],  # Enlève "LD"
                    "free": free_amt,
                    "locked": locked_amt
                })
            else:
                available_assets.append({
                    "asset": asset,
                    "free": free_amt,
                    "locked": locked_amt
                })

        db.user_portfolios.update_one(
            {"username": username},
            {
                "$set": {
                    "binance_balances": {
                        "available": available_assets,
                        "loan_debt": loan_debt_assets
                    }
                }
            },
            upsert=True
        )
        print(f"Soldes Binance mis à jour pour {username}")

    except Exception as e:
        print("Erreur API Binance :", e)


def fetch_and_update_portfolio_value(username: str, fernet: Fernet, db: MongoClient) -> None:
    client_binance = get_binance_client(username, fernet)
    portfolio = db.user_portfolios.find_one({"username": username})
    if not portfolio or "binance_balances" not in portfolio:
        print(f"Portefeuille Binance introuvable pour {username}")
        return

    available = portfolio["binance_balances"].get("available", [])
    loan_debt = portfolio["binance_balances"].get("loan_debt", [])

    total_value = 0.0

    # Fonction pour récupérer le prix USDT d'un asset
    def get_price_usdt(asset):
        if asset == "USDT":
            return 1.0
        symbol = asset + "USDT"
        try:
            ticker = client_binance.get_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except Exception:
            # Si la paire n'existe pas, on retourne 0 (ou tu peux essayer une autre paire)
            return 0.0

    # Mettre à jour les valeurs dans une liste
    def update_assets_value(assets_list):
        updated = []
        for asset_data in assets_list:
            asset = asset_data["asset"]
            free = asset_data["free"]
            locked = asset_data["locked"]
            price = get_price_usdt(asset)
            value = (free + locked) * price
            total_value_nonlocal = value  # local temporaire

            asset_data["value"] = value
            updated.append(asset_data)
            nonlocal total_value
            total_value += value
        return updated

    available = update_assets_value(available)
    loan_debt = update_assets_value(loan_debt)

    db.user_portfolios.update_one(
        {"username": username},
        {"$set": {
            "binance_balances.available": available,
            "binance_balances.loan_debt": loan_debt,
            "binance_balances.total_portfolio_value": total_value
        }}
    )
    print(f"Valeur totale du portefeuille mise à jour pour {username}: {total_value:.2f} USDT")



if __name__ == "__main__":
    FERNET_KEY = os.getenv("FERNET_KEY")
    if not FERNET_KEY:
        raise Exception("FERNET_KEY non défini dans .env")

    fernet = Fernet(FERNET_KEY.encode())

    client_mongo = MongoClient("mongodb://localhost:27017")
    db = client_mongo.krypto

    fetch_and_store_balances("VBenoit", fernet, db)
    fetch_and_update_portfolio_value("VBenoit", fernet, db)
