import pytest
from wallet import wallet


def test_create_and_sign(tmp_path):
    path = str(tmp_path / "w.json")
    w = wallet.create_wallet("haslo123", path)
    assert wallet.load_wallet(path)["address"] == w["address"]
    assert wallet.sign_message(w, "haslo123", "abc")


def test_wrong_password(tmp_path):
    path = str(tmp_path / "w.json")
    w = wallet.create_wallet("dobre", path)
    with pytest.raises(ValueError):
        wallet.sign_message(w, "zle", "abc")


def test_cannot_overwrite(tmp_path):
    path = str(tmp_path / "w.json")
    wallet.create_wallet("haslo", path)
    with pytest.raises(FileExistsError):
        wallet.create_wallet("haslo", path)