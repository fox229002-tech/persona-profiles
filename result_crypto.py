"""Fernet encryption for temporary «Образы» results. No Streamlit dependency."""

from cryptography.fernet import Fernet, InvalidToken


def generate_key() -> str:
    """Generate a URL-safe key; store it only in Streamlit secrets."""
    return Fernet.generate_key().decode("ascii")


def encrypt_result(plaintext: str, key: str) -> str:
    if not isinstance(plaintext, str):
        raise TypeError("Result must be text")
    return Fernet(key.encode("ascii")).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_result(ciphertext: str, key: str) -> str:
    return Fernet(key.encode("ascii")).decrypt(ciphertext.encode("ascii")).decode("utf-8")


def self_test() -> dict:
    key = generate_key()
    original = "Образы — тестовый профиль. Символы: ё, ✓, 🌿"
    encrypted = encrypt_result(original, key)
    assert encrypted != original
    assert decrypt_result(encrypted, key) == original
    wrong_key_rejected = False
    try:
        decrypt_result(encrypted, generate_key())
    except InvalidToken:
        wrong_key_rejected = True
    assert wrong_key_rejected
    tampered = encrypted[:-5] + ("A" if encrypted[-5] != "A" else "B") + encrypted[-4:]
    tampering_rejected = False
    try:
        decrypt_result(tampered, key)
    except InvalidToken:
        tampering_rejected = True
    assert tampering_rejected
    return {"roundtrip": "passed", "wrong_key": "denied", "tampering": "denied"}


if __name__ == "__main__":
    print(self_test())
