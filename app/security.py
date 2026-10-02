"""Password hashing (Argon2) and JWT access tokens (HS256).

Never store, log or return a password or its hash.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_password_hasher = PasswordHasher()

# Same PasswordHasher instance as real hashes, so verifying against this
# fixed dummy hash takes the same time as verifying a real one. Used when
# the account doesn't exist, so login can't be timed to reveal that it
# doesn't -- never derived from a real user's password.
_DUMMY_HASH = _password_hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a password against its hash.

    Pass None for password_hash when the account doesn't exist -- verifies
    against a fixed dummy hash instead, so this call takes the same time
    either way.
    """
    try:
        _password_hasher.verify(password_hash or _DUMMY_HASH, password)
    except VerifyMismatchError:
        return False
    return True


def create_access_token(*, user_id: int, restaurant_id: int, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    # algorithms is pinned, never read from the token itself (a token can't
    # pick its own verification algorithm); exp is required, not optional.
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp"]},
    )
