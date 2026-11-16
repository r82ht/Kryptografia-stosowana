"""Wezel sieci
    python -m node.node --port 5001 --miner-pubkey <PUBKEY> --wallet wallet_data/wallet.json
    python -m node.node --port 5002 --miner-pubkey <PUBKEY> --bootstrap http://127.0.0.1:5001
    python -m node.node --port 5003 --miner-pubkey <PUBKEY> --bootstrap http://127.0.0.1:5001
"""
import argparse
import threading
import time
import getpass

import requests
from flask import Flask, jsonify, request

from common import crypto
from common.blockchain import Blockchain

def create_app(self_url, miner_pub, wallet_private_key=None):
    app = Flask(__name__)
    peers = set()
    lock = threading.Lock()

    address = crypto.address_from_public_key_hex(miner_pub)
    bc = Blockchain(miner_pub)
    is_miner = wallet_private_key is not None

    def add_peer(url):
        """Dodawanie peera. Zwracana true, jesli byl nowy"""
        url = url.rstrip("/")
        if url == self_url or not url.startswith(("http://", "https://")):
            return False
        with lock:
            if url in peers:
                return False
            peers.add(url)
            return True

    def notify(url, new_url):
        try:
            requests.post(f"{url}/register", json={"url": new_url}, timeout=3)
        except requests.RequestException:
            pass

    def broadcast(new_url):
        with lock:
            others = [p for p in peers if p != new_url]
        for p in others:
            threading.Thread(target=notify, args=(p, new_url), daemon=True).start()

    def send_block(url, block):
        try:
            requests.post(f"{url}/blocks", json=block, timeout=3)
        except requests.RequestException:
            pass

    def broadcast_block(block):
        with lock:
            targets = list(peers)
        for p in targets:
            threading.Thread(target=send_block, args=(p, block), daemon=True).start()

    
    def sync_from_peers():
        """Pobiera lancuchy od sasiadow i przyjmuje najdluzszy poprawny."""
        with lock:
            targets = list(peers)
        for p in targets:
            try:
                r = requests.get(f"{p}/chain", timeout=5)
                r.raise_for_status()
                if bc.replace_chain(r.json()["chain"]):
                    print("Zsynchronizowano lancuch z", p, "- dlugosc:", len(bc.snapshot()))
            except (requests.RequestException, KeyError, ValueError):
                continue


    @app.get("/info")
    def info():
        return jsonify({
            "url": self_url,
            "miner_address": address,
            "miner_public_key": miner_pub,
            "is_miner": is_miner,
            "chain_length": len(bc.snapshot()),
        })

    @app.get("/chain")
    def get_chain():
        chain = bc.snapshot()
        return jsonify({"length": len(chain), "chain": chain})
    
    @app.post("/blocks")
    def receive_block():
        block = request.get_json(silent=True)
        if not isinstance(block, dict):
            return jsonify({"error": "zly format"}), 400
        last = bc.last()
        if block.get("hash") == last["hash"]:
            return jsonify({"status": "juz mam"}), 200
        idx = block.get("index")
        if isinstance(idx, int) and idx > last["index"] + 1:
            sync_from_peers() 
            return jsonify({"status": "zsynchronizowano"}), 200
        ok, reason = bc.add_block(block)
        if not ok:
            return jsonify({"error": reason}), 400
        print("Przyjeto blok", block["index"], block["hash"][:12])
        broadcast_block(block)
        return jsonify({"status": "przyjeto"}), 201

    @app.get("/peers")
    def get_peers():
        with lock:
            return jsonify({"peers": sorted(peers)})

    @app.post("/register")
    def register():
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        if not isinstance(url, str):
            return jsonify({"error": "brak pola 'url'"}), 400
        if add_peer(url):
            broadcast(url.rstrip("/"))
        with lock:
            return jsonify({"peers": sorted(peers), "self": self_url})

    @app.post("/mine")
    def mine():
        if not is_miner:
            return jsonify({"error": "to nie jest wezel gornika"}), 403
        txs = (request.get_json(silent=True) or {}).get("transactions", [])
        if not isinstance(txs, list):
            return jsonify({"error": "Transactions musi być listą"}), 400
        block = bc.mine_block(txs, wallet_private_key)
        print("Wykopano blok", block["index"], block["hash"][:12])
        broadcast_block(block)
        return jsonify(block), 201

    def join(bootstrap_url):
        time.sleep(1)
        try:
            r = requests.post(f"{bootstrap_url}/register", json={"url": self_url}, timeout=3)
            r.raise_for_status()
        except requests.RequestException as e:
            print("Nie udalo sie polaczyc z wezlem startowym:", e)
            return
        add_peer(bootstrap_url)
        for p in r.json()["peers"]:
            if add_peer(p):
                notify(p, self_url)
        print("Dolaczono do sieci. Peers:", sorted(peers))
        sync_from_peers()

    app.join = join
    app.peers = peers
    app.blockchain = bc
    return app


def main():
    parser = argparse.ArgumentParser(description="Wezel kryptowaluty")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--bootstrap", help="adres wezla startowego")
    parser.add_argument("--miner-pubkey", required=True, help="klucz publiczny gornika (hex)")
    parser.add_argument("--wallet", help="plik portfela - wlacza tryb gornika")
    args = parser.parse_args()

    private_key = None
    if args.wallet:
        from wallet.wallet import load_wallet, unlock_private_key
        try:
            wallet = load_wallet(args.wallet)
            private_key = unlock_private_key(wallet, getpass.getpass("Haslo: "))
        except FileNotFoundError:
            raise SystemExit(f"Brak pliku portfela: {args.wallet}")
        except ValueError as e:
            raise SystemExit(f"Blad: {e}")
        if crypto.public_key_to_hex(private_key.public_key()) != args.miner_pubkey:
            raise SystemExit("Klucz z portfela nie pasuje do --miner-pubkey")

    self_url = f"http://127.0.0.1:{args.port}"
    app = create_app(self_url, args.miner_pubkey, private_key)
    if args.bootstrap:
        threading.Thread(target=app.join, args=(args.bootstrap.rstrip("/"),), daemon=True).start()
    app.run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()