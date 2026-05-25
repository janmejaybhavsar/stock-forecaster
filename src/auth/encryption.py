"""
Fernet symmetric encryption for sensitive data (API keys).
Uses the JWT secret as the base key material, derived via HKDF.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config.settings import get_settings


def _get_fernet() -> Fernet:
    """Derive a Fernet key from the JWT secret (stable across restarts)."""
    settings = get_settings()
    # Derive a 32-byte key from the JWT secret using SHA-256
    key_material = hashlib.sha256(settings.jwt_secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_material)
    return Fernet(fernet_key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string, return base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string back to plaintext. Returns empty on failure."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        return ""
