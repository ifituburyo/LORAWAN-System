"""AppKey encryption at rest using Fernet (AES-128-CBC + HMAC)."""

from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()


def _get_cipher() -> Fernet:
    """Build a Fernet cipher from the configured key."""
    return Fernet(settings.appkey_encryption_key.encode())


def encrypt_app_key(plaintext: str) -> str:
    """Encrypt an AppKey (32 hex chars) for database storage."""
    cipher = _get_cipher()
    return cipher.encrypt(plaintext.encode()).decode()


def decrypt_app_key(ciphertext: str) -> str:
    """Decrypt an AppKey from database storage."""
    cipher = _get_cipher()
    return cipher.decrypt(ciphertext.encode()).decode()
