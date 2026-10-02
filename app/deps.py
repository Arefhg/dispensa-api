import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.errors import UnauthorizedError
from app.models import User
from app.security import decode_access_token

# TEMPORARY until real auth lands in week 6 (see ROADMAP.md).
# get_current_restaurant_id() is the ONLY place "whose data is this request
# for" gets decided. Every router depends on it instead of trusting a
# restaurant_id from the request body or URL. When real auth arrives, only
# this function changes (JWT -> restaurant_id) -- no router changes.


def get_current_restaurant_id() -> int:
    if settings.environment != "development":
        raise RuntimeError(
            "get_current_restaurant_id() is a development-only placeholder "
            f"and must never run with ENVIRONMENT={settings.environment!r}."
        )
    if settings.dev_restaurant_id is None:
        raise RuntimeError(
            "DEV_RESTAURANT_ID is not set. Run scripts/seed_dev.py and put the printed id in .env."
        )
    return settings.dev_restaurant_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from the Authorization header.

    The token only proves WHO the user is (user_id). Role, restaurant_id
    and is_active always come from the database, never from the token's
    own claims -- so a role change or deactivation takes effect
    immediately, not after the token's expiry.
    """
    if token is None:
        raise UnauthorizedError("Could not validate credentials.")

    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Could not validate credentials.") from None

    user_id = payload.get("user_id")
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise UnauthorizedError("Could not validate credentials.")

    return user
