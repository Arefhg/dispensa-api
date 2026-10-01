from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_restaurant_id
from app.models import Supplier
from app.schemas import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import suppliers as suppliers_service

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> list[Supplier]:
    return suppliers_service.list_suppliers(db, restaurant_id, limit, offset)


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Supplier:
    return suppliers_service.create_supplier(db, restaurant_id, data)


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Supplier:
    return suppliers_service.get_supplier(db, restaurant_id, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> Supplier:
    return suppliers_service.update_supplier(db, restaurant_id, supplier_id, data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    restaurant_id: int = Depends(get_current_restaurant_id),
) -> None:
    suppliers_service.archive_supplier(db, restaurant_id, supplier_id)
