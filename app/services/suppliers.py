from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Supplier
from app.schemas import SupplierCreate, SupplierUpdate


def list_suppliers(db: Session, restaurant_id: int, limit: int, offset: int) -> list[Supplier]:
    stmt = (
        select(Supplier)
        .where(Supplier.restaurant_id == restaurant_id, Supplier.archived_at.is_(None))
        .order_by(Supplier.name)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def create_supplier(db: Session, restaurant_id: int, data: SupplierCreate) -> Supplier:
    supplier = Supplier(restaurant_id=restaurant_id, **data.model_dump())
    db.add(supplier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"A supplier named '{data.name}' already exists.") from exc
    db.refresh(supplier)
    return supplier


def get_supplier(db: Session, restaurant_id: int, supplier_id: int) -> Supplier:
    stmt = select(Supplier).where(
        Supplier.id == supplier_id, Supplier.restaurant_id == restaurant_id
    )
    supplier = db.scalars(stmt).first()
    if supplier is None:
        raise NotFoundError(f"Supplier {supplier_id} not found.")
    return supplier


def update_supplier(
    db: Session, restaurant_id: int, supplier_id: int, data: SupplierUpdate
) -> Supplier:
    supplier = get_supplier(db, restaurant_id, supplier_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"A supplier named '{data.name}' already exists.") from exc
    db.refresh(supplier)
    return supplier


def archive_supplier(db: Session, restaurant_id: int, supplier_id: int) -> None:
    supplier = get_supplier(db, restaurant_id, supplier_id)
    if supplier.archived_at is None:
        supplier.archived_at = datetime.now(UTC)
        db.commit()
