import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# Clé de chiffrement AES générée une fois et stockée dans .env
SECRET_KEY = os.getenv("SECRET_KEY")

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY not found in .env")

fernet = Fernet(SECRET_KEY)
