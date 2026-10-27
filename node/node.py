"""Wezel sieci
    python -m node.node --port 5001
    python -m node.node --port 5002 --bootstrap http://127.0.0.1:5001
    python -m node.node --port 5003 --bootstrap http://127.0.0.1:5001
"""
import argparse
import threading
import time

import requests
from flask import Flask, jsonify, request

from common import crypto

def create_app(self_url):
    app = Flask(__name__)
    peers = set()
    lock = threading.Lock()

    private_key = crypto.generate_private_key()
    public_key = crypto.public_key_to_hex(private_key.public_key())
    address = crypto.address_from_public_key_hex(public_key)

    def add_peer(url):
        """Dodaje peera. Zwraca True, jesli byl nowy."""
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

    @app.get("/info")
    def info():
        return jsonify({"url": self_url, "address": address, "public_key": public_key})

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

    def join(bootstrap_url):
        time.sleep(1)  # poczekaj, az serwer wystartuje
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

    app.join = join
    app.peers = peers
    return app


def main():
    parser = argparse.ArgumentParser(description="Wezel kryptowaluty")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--bootstrap", help="adres wezla startowego")
    args = parser.parse_args()

    self_url = f"http://127.0.0.1:{args.port}"
    app = create_app(self_url)
    if args.bootstrap:
        threading.Thread(target=app.join, args=(args.bootstrap.rstrip("/"),), daemon=True).start()
    app.run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()