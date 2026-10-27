import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def random_base62(length: int) -> str:
    return "".join(secrets.choice(BASE62) for _ in range(length))


def hash_secret(value: str, secret_key: str) -> str:
    return hmac.new(secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"pbkdf2_sha256$240000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: str, role: str, secret_key: str, ttl_seconds: int) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "AT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": user_id, "role": role, "exp": int(time.time()) + ttl_seconds}, separators=(",", ":")).encode())
    body = f"{header}.{payload}"
    signature = _b64(hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        body = f"{header}.{payload}"
        expected = _b64(hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) < int(time.time()):
            raise ValueError("expired token")
        return claims
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError("invalid access token") from None
