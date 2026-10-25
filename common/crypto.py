import hashlib
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import time
import os
SCRYPT_COST = 2**15
SCRYPT_BLOCK_SIZE = 8
SCRYPT_PARALLELISM = 1

def generate_private_key():
    private_key = ec.generate_private_key(ec.SECP256K1())
    return private_key


def public_key_to_hex(public_key):
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    return public_key_bytes.hex()


def public_key_from_hex(public_key_hex):
    public_key_bytes = bytes.fromhex(public_key_hex)
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256K1(), public_key_bytes
    )
    return public_key


def address_from_public_key_hex(public_key_hex):
    public_key_bytes = bytes.fromhex(public_key_hex)
    address = hashlib.sha256(public_key_bytes).hexdigest()[:40]
    return address


def sign(private_key, message):
    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    return signature.hex()


def verify(public_key_hex, message, signature_hex):
    try:
        public_key = public_key_from_hex(public_key_hex)
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError):
        return False

def derive_key(password, salt, n, r, p):
    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return kdf.derive(password.encode())

    
def encrypt_private_key(private_key, password):
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_key(password, salt, SCRYPT_COST, SCRYPT_BLOCK_SIZE, SCRYPT_PARALLELISM)
    ciphertext = AESGCM(key).encrypt(nonce, private_key_bytes, None)
    return {
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex(),
        "cost": SCRYPT_COST,
        "block_size": SCRYPT_BLOCK_SIZE,
        "parallelism": SCRYPT_PARALLELISM,
    }

def decrypt_private_key(data, password):
    salt = bytes.fromhex(data["salt"])
    nonce = bytes.fromhex(data["nonce"])
    ciphertext = bytes.fromhex(data["ciphertext"])
    key = derive_key(password, salt, data["cost"], data["block_size"], data["parallelism"])
    try:
        private_key_bytes = AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError("Zle haslo lub uszkodzony plik")
    return serialization.load_der_private_key(private_key_bytes, password=None)