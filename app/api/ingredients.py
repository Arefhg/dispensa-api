from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_restaurant_id
from app.models import Ingredient
from app.schemas import IngredientCreate, IngredientRead, IngredientUpdate
from app.services import ingredients as ingredients_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientRead])
def list_ingredients(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> list[Ingredient]:
    return ingredients_service.list_ingredients(db, restaurant_id, limit, offset)


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: IngredientCreate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Ingredient:
    return ingredients_service.create_ingredient(db, restaurant_id, data)


@router.get("/{ingredient_id}", response_model=IngredientRead)
def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Ingredient:
    return ingredients_service.get_ingredient(db, restaurant_id, ingredient_id)


@router.patch("/{ingredient_id}", response_model=IngredientRead)
def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Ingredient:
    return ingredients_service.update_ingredient(db, restaurant_id, ingredient_id, data)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> None:
    ingredients_service.archive_ingredient(db, restaurant_id, ingredient_id)
