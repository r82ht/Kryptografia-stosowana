from common import crypto
from node.node import create_app

MINER_PUB = crypto.public_key_to_hex(crypto.generate_private_key().public_key())


def make_client():
    return create_app("http://127.0.0.1:5001", MINER_PUB).test_client()


def test_register_adds_peer():
    c = make_client()
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    assert c.get("/peers").get_json()["peers"] == ["http://127.0.0.1:5002"]


def test_register_duplicate_no_double_entry():
    c = make_client()
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    assert c.get("/peers").get_json()["peers"] == ["http://127.0.0.1:5002"]


def test_register_without_url_returns_400():
    c = make_client()
    assert c.post("/register", json={}).status_code == 400