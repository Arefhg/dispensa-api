from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Restaurant, User
from app.schemas import (
    AccountResponse,
    LoginRequest,
    RegisterRequest,
    RestaurantRead,
    TokenResponse,
    UserRead,
)
from app.security import create_access_token
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> AccountResponse:
    user, restaurant = auth_service.register(db, data)
    return AccountResponse(
        user=UserRead.model_validate(user), restaurant=RestaurantRead.model_validate(restaurant)
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.login(db, data)
    token = create_access_token(user_id=user.id, restaurant_id=user.restaurant_id, role=user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AccountResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    restaurant = db.get(Restaurant, current_user.restaurant_id)
    assert restaurant is not None, "restaurant_id FK guarantees this row exists"
    return AccountResponse(
        user=UserRead.model_validate(current_user),
        restaurant=RestaurantRead.model_validate(restaurant),
    )
