import hashlib
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


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


def main():
    k = generate_private_key()
    pub = public_key_to_hex(k.public_key())
    podpis = sign(k, b"abc")

    print(pub, len(pub))
    print(address_from_public_key_hex(pub))
    print(verify(pub, b"abc", podpis))
    print(verify(pub, b"abd", podpis))


if __name__ == "__main__":
    main()