from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import hashlib


def generate_private_key():
    key = ec.generate_private_key(ec.SECP256K1())
    return key

def public_key_to_hex(pub):
    key_hexed = pub.public_bytes(encoding=serialization.Encoding.X962, format=serialization.PublicFormat.CompressedPoint)
    return key_hexed.hex()

def public_key_from_hex(pub):
    key_bytes = bytes.fromhex(pub)
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), key_bytes)
    return public_key

def address_from_public_key_hex(key_hexed):
    key_bytes = bytes.fromhex(key_hexed)
    address = hashlib.sha256(key_bytes).hexdigest()[:40]
    return address

def main():
    k = generate_private_key()
    h = public_key_to_hex(k.public_key())
    b = public_key_from_hex(h)
    print(h)
    print(b)
    print(len(h))


if __name__ == "__main__":
    main()