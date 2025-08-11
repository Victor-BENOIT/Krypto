from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from passlib.hash import bcrypt
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


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

        # Sauvegarde ou mise à jour dans la collection users
        db.users.update_one(
            {"username": username},
            {"$set": {"binance_api_key": api_key, "binance_api_secret": api_secret}}
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
    api_key = user.get("binance_api_key")
    api_secret = user.get("binance_api_secret")

    if not api_key or not api_secret:
        flash("Vous n'avez pas encore enregistré vos clés Binance.", "error")
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
