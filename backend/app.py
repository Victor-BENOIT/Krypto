from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from passlib.hash import bcrypt
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

fernet_key = os.getenv("FERNET_KEY")
if fernet_key is None:
    raise ValueError("FERNET_KEY non trouvé dans les variables d'environnement. Veuillez générer une clé Fernet et l'ajouter à votre fichier .env.")

fernet = Fernet(fernet_key.encode())

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
client = MongoClient(MONGO_URI)
db = client.krypto

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if db.users.find_one({"username": username}):
            flash("Nom d'utilisateur déjà utilisé", "error")
            return redirect(url_for("register"))
        hashed = bcrypt.hash(password)
        db.users.insert_one({"username": username, "password": hashed})
        flash("Inscription réussie, vous pouvez maintenant vous connecter", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = db.users.find_one({"username": username})
        if user and bcrypt.verify(password, user["password"]):
            session["username"] = username  # <-- Sauvegarde de la session
            flash(f"Bienvenue {username} !", "success")
            return redirect(url_for("index"))
        flash("Nom d'utilisateur ou mot de passe invalide", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Déconnecté", "success")
    return redirect(url_for("index"))


@app.route("/connect_binance", methods=["GET", "POST"])
def connect_binance():
    # Pour l'instant, on ne gère pas la session utilisateur, on suppose que username est 'guest'
    # Idéalement, tu gères la session pour récupérer l'utilisateur connecté
    username = session.get("username", None)
    if not username:
        flash("Vous devez être connecté pour connecter Binance", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        api_key = request.form["api_key"].strip()
        api_secret = request.form["api_secret"].strip()

        encrypted_api_key = fernet.encrypt(api_key.encode()).decode()
        encrypted_api_secret = fernet.encrypt(api_secret.encode()).decode()

        db.users.update_one(
            {"username": username},
            {"$set": {"binance_api_key": encrypted_api_key, "binance_api_secret": encrypted_api_secret}}
        )

        flash("Clés Binance enregistrées avec succès !", "success")
        return redirect(url_for("index"))

    return render_template("connect_binance.html")


@app.route("/test_binance_key", methods=["POST"])
def test_binance_key():
    username = session.get("username")
    if not username:
        flash("Vous devez être connecté pour tester la clé Binance.", "error")
        return redirect(url_for("login"))

    user = db.users.find_one({"username": username})
    encrypted_api_key = user.get("binance_api_key")
    encrypted_api_secret = user.get("binance_api_secret")

    if not encrypted_api_key or not encrypted_api_secret:
        flash("Vous n'avez pas encore enregistré vos clés Binance.", "error")
        return redirect(url_for("connect_binance"))

    try:
        api_key = fernet.decrypt(encrypted_api_key.encode()).decode()
        api_secret = fernet.decrypt(encrypted_api_secret.encode()).decode()
    except Exception as e:
        flash("Erreur lors du déchiffrement des clés Binance.", "error")
        return redirect(url_for("connect_binance"))

    try:
        client = Client(api_key, api_secret)
        # Test simple : récupérer le solde du compte (spot account)
        account_info = client.get_account()
        # Si on arrive ici, la clé est valide
        flash("Clé Binance valide et fonctionnelle !", "success")
    except (BinanceAPIException, BinanceRequestException) as e:
        flash(f"Erreur avec la clé Binance : {str(e)}", "error")
    except Exception as e:
        flash(f"Erreur inattendue : {str(e)}", "error")

    return redirect(url_for("index"))

@app.route('/portfolio')
def portfolio():
    # Ici on suppose que username est en session (géré après login)
    username = session.get("username")
    if not username:
        return redirect(url_for('login'))

    # fetch_and_store_balances("username", fernet, db)
    # fetch_and_update_portfolio_value("username", fernet, db)
    user_portfolio = db.user_portfolios.find_one({"username": username})
    if not user_portfolio or "binance_balances" not in user_portfolio:
        assets_available = []
        assets_loan_debt = []
        total_value = 0
    else:
        assets_available = user_portfolio["binance_balances"].get("available", [])
        assets_loan_debt = user_portfolio["binance_balances"].get("loan_debt", [])
        total_value = user_portfolio["binance_balances"].get("total_portfolio_value", 0)

    return render_template(
        "portfolio.html",
        assets_available=assets_available,
        assets_loan_debt=assets_loan_debt,
        total_value=total_value,
        username=username
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)