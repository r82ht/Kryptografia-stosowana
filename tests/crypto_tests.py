import os
import pytest
from common import crypto

def test_public_key_hex_format():
    key = crypto.generate_private_key()
    key_h = crypto.public_key_to_hex(key.public_key())
    assert len(key_h) == 66 #33 bajty * 2 (1 na prefiks + 32 na parametr x w krzywej)
    
def test_public_key_hex_roundtrip():
    key = crypto.generate_private_key()
    key_h = crypto.public_key_to_hex(key.public_key())
    assert crypto.public_key_to_hex(crypto.public_key_from_hex(key_h)) == key_h # zamiana klucz - hex - klucz -hex

def test_public_key_from_invalid_hex_raises():
    with pytest.raises(ValueError):
        crypto.public_key_from_hex("losowy_String_ktoryyy_nie_jest_hex") # to nie hex
    with pytest.raises(ValueError):
        crypto.public_key_from_hex("abcd") # to jest hex ale za krotki na klucz

def test_address_format_and_uniqueness():
    key_h1 = crypto.public_key_to_hex(crypto.generate_private_key().public_key())
    key_h2 = crypto.public_key_to_hex(crypto.generate_private_key().public_key())
    assert len(crypto.address_from_public_key_hex(key_h1)) == 40 # czy poprawna dlugosc klucza
    assert crypto.address_from_public_key_hex(key_h1) != crypto.address_from_public_key_hex(key_h2) # czy wygenerowano dwa rozne klucze publiczne


def test_sign_and_verify_ok():
    key = crypto.generate_private_key()
    pub = crypto.public_key_to_hex(key.public_key())
    signature = crypto.sign(key, b"abc")
    assert crypto.verify(pub, b"abc", signature) is True # podano dobre dane
 
 
def test_verify_modified_message():
    key = crypto.generate_private_key()
    pub = crypto.public_key_to_hex(key.public_key())
    signature = crypto.sign(key, b"abc")
    assert crypto.verify(pub, b"abd", signature) is False # zmodyfikowano wiadomosc
 
 
def test_verify_wrong_public_key():
    key = crypto.generate_private_key()
    other_pub = crypto.public_key_to_hex(crypto.generate_private_key().public_key())
    signature = crypto.sign(key, b"abc")
    assert crypto.verify(other_pub, b"abc", signature) is False # zly klucz


def test_verify_bad_input_returns_false():
    key = crypto.generate_private_key()
    pub = crypto.public_key_to_hex(key.public_key())
    signature = crypto.sign(key, b"abc")
    assert crypto.verify(pub, b"abc", "00" + signature[2:]) is False # uszkodzony podpis
    assert crypto.verify(pub, b"abc", "to_nie_hex") is False # podpis nie jest w hex
    assert crypto.verify("zly_klucz", b"abc", signature) is False # podano zly klucz


def test_encrypt_returns_expected_fields():
    data = crypto.encrypt_private_key(crypto.generate_private_key(), "haslo123")
    assert len(data["salt"]) == 32 # 16 bajtow
    assert len(data["nonce"]) == 24 # 12 bajtow
    assert isinstance(data["ciphertext"], str) # czy na pewno to pole to string

def test_encrypt_decrypt_roundtrip():
    key = crypto.generate_private_key()
    pub = crypto.public_key_to_hex(key.public_key())
    data = crypto.encrypt_private_key(key, "haslo123")
    restored = crypto.decrypt_private_key(data, "haslo123")
    assert crypto.public_key_to_hex(restored.public_key()) == pub # odtworzony klucz jest taki sam
    assert crypto.verify(pub, b"abc", crypto.sign(restored, b"abc")) is True 

def test_wrong_password_raises():
    data = crypto.encrypt_private_key(crypto.generate_private_key(), "dobre")
    with pytest.raises(ValueError):
        crypto.decrypt_private_key(data, "zle") # odszyfrowywanie zlym haslem

def test_each_encryption_is_different():
    key = crypto.generate_private_key()
    d1 = crypto.encrypt_private_key(key, "haslo")
    d2 = crypto.encrypt_private_key(key, "haslo")
    assert d1["salt"] != d2["salt"] # obie sole sa rozne
    assert d1["nonce"] != d2["nonce"] # oba nonce sa rozne