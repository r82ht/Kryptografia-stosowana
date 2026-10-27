from node.node import create_app


def test_register_adds_peer():
    c = create_app("http://127.0.0.1:5001").test_client()
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    assert c.get("/peers").get_json()["peers"] == ["http://127.0.0.1:5002"]


def test_register_duplicate_no_double_entry():
    c = create_app("http://127.0.0.1:5001").test_client()
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    c.post("/register", json={"url": "http://127.0.0.1:5002"})
    assert c.get("/peers").get_json()["peers"] == ["http://127.0.0.1:5002"]


def test_register_without_url_returns_400():
    c = create_app("http://127.0.0.1:5001").test_client()
    assert c.post("/register", json={}).status_code == 400