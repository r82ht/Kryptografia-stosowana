"""Portfel - klient wezla
    python -m wallet.wallet create
    python -m wallet.wallet info
    python -m wallet.wallet sign "tresc wiadomosci"
    python -m wallet.wallet peers --node http://127.0.0.1:5001
"""

import argparse
import getpass
import json
import os
import sys
import requests
from common import crypto


WALLET_DIR = "wallet_data"
WALLET_FILE = os.path.join(WALLET_DIR, "wallet.json")


def save_wallet(wallet, path=WALLET_FILE):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(wallet, f, indent=2)

def load_wallet(path=WALLET_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def create_wallet(password, path=WALLET_FILE):
    if os.path.exists(path):
        raise FileExistsError(f"Portfel juz istnieje: {path}")
    if not password:
        raise ValueError("Haslo nie moze byc puste")

def create_wallet(password, path=WALLET_FILE):
    if os.path.exists(path):
        raise FileExistsError(f"Portfel juz istnieje: {path}")
    if not password:
        raise ValueError("Haslo nie moze byc puste")
    private_key = crypto.generate_private_key()
    public_key_hex = crypto.public_key_to_hex(private_key.public_key())
    wallet = {
        "address": crypto.address_from_public_key_hex(public_key_hex),
        "public_key": public_key_hex,
        "encrypted_private_key": crypto.encrypt_private_key(private_key, password),
    }
    save_wallet(wallet, path)
    return wallet

# odszyfrowuje klucz prywatny. Przy zlym hasle rzuca ValueError
def unlock_private_key(wallet, password):
    return crypto.decrypt_private_key(wallet["encrypted_private_key"], password)

# podpisuje tekst kluczem z portfela, zwraca podpis jako hex
def sign_message(wallet, password, text):
    private_key = unlock_private_key(wallet, password)
    return crypto.sign(private_key, text.encode())

def ask_new_password():
    password = getpass.getpass("Ustaw haslo do portfela: ")
    if password != getpass.getpass("Powtorz haslo: "):
        raise ValueError("Hasla sie roznia")
    return password

def get_peers(node_url):
    r = requests.get(f"{node_url}/peers", timeout=3)
    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser(description="Portfel kryptowaluty")
    parser.add_argument("--file", default=WALLET_FILE, help="sciezka pliku portfela")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("create", help="utworz nowy portfel")
    sub.add_parser("info", help="pokaz adres i klucz publiczny")
    p_sign = sub.add_parser("sign", help="podpisz tekst")
    p_sign.add_argument("message")
    p_peers = sub.add_parser("peers", help="zapytaj wezel o sasiadow")
    p_peers.add_argument("--node", default="http://127.0.0.1:5001")
    args = parser.parse_args()

    try:
        if args.cmd == "create":
            wallet = create_wallet(ask_new_password(), args.file)
            print("Utworzono portfel.")
            print("Adres: ", wallet["address"])
        elif args.cmd == "info":
            wallet = load_wallet(args.file)
            print("Adres: ", wallet["address"])
            print("Klucz publczny: ", wallet["public_key"])
        elif args.cmd == "sign":
            wallet = load_wallet(args.file)
            signature = sign_message(wallet, getpass.getpass("Haslo: "), args.message)
            print("Podpis:", signature)
            ok = crypto.verify(wallet["public_key"], args.message.encode(), signature)
            print("Weryfikacja: ", ok)
        elif args.cmd == "peers":
            print(json.dumps(get_peers(args.node), indent=2))
    except FileNotFoundError:
        print("Brak portfela. Najpierw uruchom: python -m wallet.wallet create")
        sys.exit(1)
    except FileExistsError as e:
        print("Blad:", e)
        sys.exit(1)
    except ValueError as e:
        print("Blad:", e)
        sys.exit(1)
    except requests.RequestException as e:
        print("Nie mozna polaczyc z wezlem:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()