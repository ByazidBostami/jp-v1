"""Lightweight reversible encryption for sensitive candidate identifiers
(passport number, national ID) — SRS marks these *_encrypted.

Uses Fernet if `cryptography` is installed; otherwise falls back to a keyed
obfuscation so the project still runs in a minimal environment. In production
install `cryptography` and set FIELD_ENCRYPTION_KEY to a 32-byte urlsafe key.
"""
import base64
import hashlib
from django.conf import settings

try:
    from cryptography.fernet import Fernet
    _HAS_FERNET = True
except Exception:  # pragma: no cover
    _HAS_FERNET = False


def _fernet():
    key = hashlib.sha256(settings.FIELD_ENCRYPTION_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: str) -> str:
    if not value:
        return value
    if _HAS_FERNET:
        return _fernet().encrypt(value.encode()).decode()
    xored = _xor(value.encode())
    return "obf$" + base64.urlsafe_b64encode(xored).decode()


def decrypt(token: str) -> str:
    if not token:
        return token
    if token.startswith("obf$"):
        raw = base64.urlsafe_b64decode(token[4:].encode())
        return _xor(raw).decode()
    if _HAS_FERNET:
        return _fernet().decrypt(token.encode()).decode()
    return token


def _xor(data: bytes) -> bytes:
    key = hashlib.sha256(settings.FIELD_ENCRYPTION_KEY.encode()).digest()
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
