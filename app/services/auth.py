from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, UnauthorizedError
from app.models import Restaurant, User
from app.schemas import LoginRequest, RegisterRequest
from app.security import hash_password, verify_password


def register(db: Session, data: RegisterRequest) -> tuple[User, Restaurant]:
    restaurant = Restaurant(name=data.restaurant_name, address=data.restaurant_address)
    db.add(restaurant)
    db.flush()  # assigns restaurant.id, within the same not-yet-committed transaction

    user = User(
        restaurant_id=restaurant.id,
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role="owner",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"An account with email '{data.email}' already exists.") from exc
    db.refresh(user)
    db.refresh(restaurant)
    return user, restaurant


def login(db: Session, data: LoginRequest) -> User:
    user = db.scalars(select(User).where(User.email == data.email)).first()
    password_hash = user.password_hash if user is not None else None

    # Always run exactly one Argon2 verify, real or dummy, before deciding
    # anything -- checking is_active first would let a deactivated account
    # fail faster than a wrong-password one, leaking via timing exactly
    # what the generic error message is meant to hide.
    password_ok = verify_password(data.password, password_hash)

    if user is None or not password_ok or not user.is_active:
        raise UnauthorizedError("Invalid email or password.")

    return user
