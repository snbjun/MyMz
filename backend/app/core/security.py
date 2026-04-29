import hashlib
import hmac
import base64
import json
import secrets
import time
from datetime import timedelta

from app.core.config import settings


def hash_password(password: str) -> str:
    """第 2 阶段沿用骨架密码哈希：从静态登录改为真实密码校验。"""

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, digest = password_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return hmac.compare_digest(candidate, digest)


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """第 2 阶段新增：生成 HS256 JWT，避免引入额外运行时依赖。"""

    expire_seconds = int(
        time.time()
        + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes)).total_seconds()
    )
    header = {"alg": settings.algorithm, "typ": "JWT"}
    payload = {"sub": subject, "exp": expire_seconds}
    header_segment = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, object]:
    """第 2 阶段新增：校验 JWT 签名与过期时间，失败时统一抛出 ValueError。"""

    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected = hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        received = _base64url_decode(signature_segment)
        if not hmac.compare_digest(expected, received):
            raise ValueError("Invalid token signature")

        header = json.loads(_base64url_decode(header_segment))
        if header.get("alg") != settings.algorithm:
            raise ValueError("Unsupported token algorithm")

        payload = json.loads(_base64url_decode(payload_segment))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except (ValueError, json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("Invalid token") from None
