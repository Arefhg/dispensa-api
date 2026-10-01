from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Ingredient
from app.schemas import IngredientCreate, IngredientUpdate


def list_ingredients(db: Session, restaurant_id: int, limit: int, offset: int) -> list[Ingredient]:
    stmt = (
        select(Ingredient)
        .where(Ingredient.restaurant_id == restaurant_id, Ingredient.archived_at.is_(None))
        .order_by(Ingredient.name)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def create_ingredient(db: Session, restaurant_id: int, data: IngredientCreate) -> Ingredient:
    ingredient = Ingredient(restaurant_id=restaurant_id, **data.model_dump())
    db.add(ingredient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"An ingredient named '{data.name}' already exists.") from exc
    db.refresh(ingredient)
    return ingredient


def get_ingredient(db: Session, restaurant_id: int, ingredient_id: int) -> Ingredient:
    stmt = select(Ingredient).where(
        Ingredient.id == ingredient_id, Ingredient.restaurant_id == restaurant_id
    )
    ingredient = db.scalars(stmt).first()
    if ingredient is None:
        raise NotFoundError(f"Ingredient {ingredient_id} not found.")
    return ingredient


def update_ingredient(
    db: Session, restaurant_id: int, ingredient_id: int, data: IngredientUpdate
) -> Ingredient:
    ingredient = get_ingredient(db, restaurant_id, ingredient_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ingredient, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"An ingredient named '{data.name}' already exists.") from exc
    db.refresh(ingredient)
    return ingredient


def archive_ingredient(db: Session, restaurant_id: int, ingredient_id: int) -> None:
    ingredient = get_ingredient(db, restaurant_id, ingredient_id)
    if ingredient.archived_at is None:
        ingredient.archived_at = datetime.now(UTC)
        db.commit()
