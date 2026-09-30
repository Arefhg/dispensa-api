from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    address: Mapped[str]
    vat_number: Mapped[str | None]
    timezone: Mapped[str] = mapped_column(server_default="Europe/Rome")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
