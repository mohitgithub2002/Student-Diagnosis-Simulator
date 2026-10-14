"""Password, PIN, OTP and token helpers.

Student PINs are 4 digits, so they are stored as a keyed HMAC scoped to the class (lookup is by class
code + PIN). Brute force is limited by the login lockout, and a leaked table is useless without the
server secret. Staff passwords use bcrypt.
"""

import base64
import hashlib
import hmac
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core.config import get_settings

ALGORITHM = "HS256"


def _secret() -> bytes:
    return get_settings().secret_key.encode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def keyed_hash(value: str, scope: str = "") -> str:
    return hmac.new(_secret(), f"{scope}:{value}".encode(), hashlib.sha256).hexdigest()


def pin_hash(class_id: int, pin: str) -> str:
    return keyed_hash(pin, scope=f"pin:{class_id}")


def phone_hash(phone: str) -> str:
    return keyed_hash(normalize_phone(phone), scope="phone")


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    return "+" + digits


def generate_pin() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(4))


def generate_otp() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


def generate_class_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def generate_token() -> str:
    return secrets.token_urlsafe(24)


def _fernet() -> Fernet:
    key = get_settings().field_encryption_key
    if not key:
        key = base64.urlsafe_b64encode(hashlib.sha256(_secret() + b"fields").digest()).decode()
    return Fernet(key.encode())


def encrypt_field(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def create_token(claims: dict[str, Any], ttl_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {**claims, "iat": now, "exp": now + timedelta(minutes=ttl_minutes)}
    return jwt.encode(payload, get_settings().secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])


def pseudonym(student_id: str) -> str:
    """Stable de-identified reference shown to internal reviewers instead of a name."""
    return "S-" + keyed_hash(student_id, scope="pseudonym")[:10].upper()
