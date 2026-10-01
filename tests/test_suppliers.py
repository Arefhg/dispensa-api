from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Restaurant, Supplier


def _create_supplier(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Fresh Produce Co"}
    payload.update(overrides)
    response = client.post("/suppliers", json=payload)
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_create_supplier(client: TestClient) -> None:
    body = _create_supplier(client, phone="+39 081 1234567", email="Orders@FreshProduce.IT")

    assert body["name"] == "Fresh Produce Co"
    assert body["phone"] == "+39 081 1234567"
    assert body["email"] == "orders@freshproduce.it"
    assert body["archived_at"] is None


def test_list_suppliers(client: TestClient) -> None:
    _create_supplier(client, name="Fresh Produce Co")
    _create_supplier(client, name="Mozzarella Imports")

    response = client.get("/suppliers")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert names == ["Fresh Produce Co", "Mozzarella Imports"]


def test_get_supplier(client: TestClient) -> None:
    created = _create_supplier(client)

    response = client.get(f"/suppliers/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_supplier(client: TestClient) -> None:
    created = _create_supplier(client)

    response = client.patch(f"/suppliers/{created['id']}", json={"phone": "+39 081 7654321"})

    assert response.status_code == 200
    assert response.json()["phone"] == "+39 081 7654321"


def test_update_email_is_lowercased(client: TestClient) -> None:
    created = _create_supplier(client)

    response = client.patch(f"/suppliers/{created['id']}", json={"email": "New@Contact.COM"})

    assert response.status_code == 200
    assert response.json()["email"] == "new@contact.com"


def test_archive_hides_from_list_but_not_from_direct_get(client: TestClient) -> None:
    created = _create_supplier(client)

    archive_response = client.delete(f"/suppliers/{created['id']}")
    assert archive_response.status_code == 204

    list_response = client.get("/suppliers")
    assert list_response.json() == []

    get_response = client.get(f"/suppliers/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["archived_at"] is not None


def test_duplicate_name_is_conflict(client: TestClient) -> None:
    _create_supplier(client, name="Fresh Produce Co")

    response = client.post("/suppliers", json={"name": "Fresh Produce Co"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_rename_to_existing_name_is_conflict(client: TestClient) -> None:
    _create_supplier(client, name="Fresh Produce Co")
    other = _create_supplier(client, name="Mozzarella Imports")

    response = client.patch(f"/suppliers/{other['id']}", json={"name": "Fresh Produce Co"})

    assert response.status_code == 409
    assert "Fresh Produce Co" in response.json()["error"]["message"]


def test_bad_email_is_invalid(client: TestClient) -> None:
    response = client.post("/suppliers", json={"name": "X", "email": "not-an-email"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_other_restaurant_cannot_read_update_or_archive(
    client: TestClient, other_restaurant: Restaurant, db_session: Session
) -> None:
    other_supplier = Supplier(restaurant_id=other_restaurant.id, name="Secret Supplier")
    db_session.add(other_supplier)
    db_session.commit()
    db_session.refresh(other_supplier)

    get_response = client.get(f"/suppliers/{other_supplier.id}")
    assert get_response.status_code == 404

    patch_response = client.patch(f"/suppliers/{other_supplier.id}", json={"phone": "000"})
    assert patch_response.status_code == 404

    delete_response = client.delete(f"/suppliers/{other_supplier.id}")
    assert delete_response.status_code == 404
