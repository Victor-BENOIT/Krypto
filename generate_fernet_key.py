from cryptography.fernet import Fernet
import os

ENV_FILE = ".env"

def generate_and_store_key():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("FERNET_KEY="):
                    print("FERNET_KEY déjà présente dans .env")
                    return

    key = Fernet.generate_key().decode()
    print(f"Génération d'une nouvelle clé Fernet : {key}")

    # On ajoute la clé à la fin du fichier .env ou on crée un nouveau fichier
    mode = "a" if os.path.exists(ENV_FILE) else "w"
    with open(ENV_FILE, mode) as f:
        if mode == "a" and not lines[-1].endswith("\n"):
            f.write("\n")
        f.write(f"FERNET_KEY={key}\n")
    print("Clé ajoutée dans .env")

if __name__ == "__main__":
    generate_and_store_key()
