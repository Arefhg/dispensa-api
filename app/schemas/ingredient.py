from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Unit = Literal["kg", "l", "pcs"]


class IngredientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    unit: Unit
    min_stock: Decimal = Field(default=Decimal("0"), ge=0)


class IngredientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    unit: Unit | None = None
    min_stock: Decimal | None = Field(default=None, ge=0)


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    unit: Unit
    min_stock: Decimal
    archived_at: datetime | None
    created_at: datetime
