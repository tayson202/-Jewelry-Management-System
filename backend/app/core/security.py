import hashlib
import hmac
import os
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from app.core.config import settings

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64url_decode(data_str: str) -> bytes:
    padding = '=' * (-len(data_str) % 4)
    return base64.urlsafe_b64decode(data_str + padding)

def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + "$" + key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt_hex, key_hex = hashed_password.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(expected_key, new_key)
    except Exception:
        return False

def get_pin_hash(pin: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 salted hash for 4-6 digit employee security PINs."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 100000)
    return salt.hex() + "$" + key.hex()

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    try:
        if not hashed_pin or "$" not in hashed_pin:
            return False
        salt_hex, key_hex = hashed_pin.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_pin.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(expected_key, new_key)
    except Exception:
        return False

def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: timedelta = None,
    token_version: int = 1
) -> str:
    """
    Signs token using strict HS256 algorithm with token_version for session revocation.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "role": role,
        "tv": int(token_version)
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> dict:
    """
    Blueprint Section 1: Strictly validates HS256 signature and token expiration.
    Guards against Algorithm Confusion attacks (rejects 'none' algorithm).
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token")

        header_b64, payload_b64, sig_b64 = parts
        header = json.loads(_b64url_decode(header_b64).decode('utf-8'))
        
        # Strict algorithm check
        if header.get("alg") != "HS256":
            raise ValueError(f"Unauthorized algorithm: {header.get('alg')}")

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid token signature")

        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise ValueError("Token expired")

        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")
