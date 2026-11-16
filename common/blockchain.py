import hashlib
import json
import threading
import time

from common import crypto

HASHED_FIELDS = ("index", "timestamp", "prev_hash", "transactions", "miner")
BLOCK_FIELDS = set(HASHED_FIELDS) | {"hash", "signature"}
MAX_FUTURE_DRIFT = 60


def block_hash(block):
    body = {}
    for k in HASHED_FIELDS:
        body[k] = block[k]
    data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

def make_genesis():
    g = {"index": 0, "timestamp": 0, "prev_hash": "0" * 64,
             "transactions": [], "miner": "", "signature": ""}
    g["hash"] = block_hash(g)
    return g

def create_block(prev, transactions, miner_hex_pub, private_key):
    block = {
        "index": prev["index"] + 1,
        "timestamp": time.time(),
        "prev_hash": prev["hash"],
        "transactions": transactions,
        "miner": miner_hex_pub,
    }
    block["hash"] = block_hash(block)
    block["signature"] = crypto.sign(private_key, block["hash"].encode())
    return block

def verify_block(block, prev, miner_pub_hex):
    """Sprawdza blok wzgledem poprzedniego. Zwraca, ze okej albo powod"""
    try:
        if not isinstance(block, dict) or set(block) != BLOCK_FIELDS:
            return False, "Niepełny lub nadmiarowy blok"
        if not isinstance(block["transactions"], list):
            return False, "Transactions musi być listą"
        if block["index"] != prev["index"] + 1:
            return False, "Nieprawidłowy index"
        if block["prev_hash"] != prev["hash"]:
            return False, "Nieprawidłowy poprzedni hash"
        if block["miner"] != miner_pub_hex:
            return False, "Nieznany górnik"
        if block["hash"] != block_hash(block):
            return False, "Nieprawidłowy hash"
        if block["timestamp"] > time.time() + MAX_FUTURE_DRIFT:
            return False, "Timestamp z przyszłości"
        if block["timestamp"] < prev["timestamp"]:
            return False, "Timestamp wsteczny"
        if not crypto.verify(miner_pub_hex, block["hash"].encode(), block["signature"]):
            return False, "Zły podpis"
    except (KeyError, TypeError, ValueError):
        return False, "Niepoprawny blok"
    return True, "ok"

     
if __name__ == "__main__":
        priv = crypto.generate_private_key()
        pub = crypto.public_key_to_hex(priv.public_key())
        zerowy = make_genesis()
        nowy = create_block(zerowy, [], pub, priv)
        print(verify_block(nowy, zerowy, pub))


class Blockchain:
    def __init__(self, miner_pub_hex):
        self.miner_pub = miner_pub_hex
        self.chain = [make_genesis()]
        self.lock = threading.Lock()

    def last(self):
        with self.lock:
            return self.chain[-1]

    def snapshot(self):
        with self.lock:
            return list(self.chain)

    def add_block(self, block):
        """Dodaje blok od innego wezla po weryfikacji. Zwraca (ok, powod)."""
        with self.lock:
            ok, reason = verify_block(block, self.chain[-1], self.miner_pub)
            if ok:
                self.chain.append(block)
            return ok, reason

    def mine_block(self, transactions, private_key):
        """Tworzy i dodaje nowy blok."""
        with self.lock:
            block = create_block(self.chain[-1], transactions, self.miner_pub, private_key)
            self.chain.append(block)
            return block

    def replace_chain(self, new_chain):
        """Przyjmuje dluższy, w pelni poprawny lancuch. Zwraca True, jeśli dodano blok i podmieniono"""
        if not isinstance(new_chain, list) or not new_chain:
            return False
        if new_chain[0] != make_genesis():
            return False
        for prev, blk in zip(new_chain, new_chain[1:]):
            if not verify_block(blk, prev, self.miner_pub)[0]:
                return False
        with self.lock:
            if len(new_chain) <= len(self.chain):
                return False
            self.chain = list(new_chain)
            return True