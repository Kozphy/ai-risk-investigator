from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Role(StrEnum):
    ADMIN = "admin"
    AUDITOR = "auditor"
    RISK_MANAGER = "risk_manager"
    COMPLIANCE = "compliance"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[Role, int] = {
    Role.VIEWER: 1,
    Role.COMPLIANCE: 2,
    Role.RISK_MANAGER: 3,
    Role.AUDITOR: 4,
    Role.ADMIN: 5,
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(subject: str, expires_delta: timedelta, token_type: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(UTC) + expires_delta,
        "iat": datetime.now(UTC),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: Role) -> str:
    settings = get_settings()
    return create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
        extra={"role": role.value},
    )


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def role_at_least(user_role: Role, required: Role) -> bool:
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required, 0)
