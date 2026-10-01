from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Ingredient, Restaurant


def _create_ingredient(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "Flour", "unit": "kg", "min_stock": 5}
    payload.update(overrides)
    response = client.post("/ingredients", json=payload)
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_create_ingredient(client: TestClient) -> None:
    body = _create_ingredient(client)

    assert body["name"] == "Flour"
    assert body["unit"] == "kg"
    assert body["min_stock"] == "5.000"
    assert body["archived_at"] is None


def test_list_ingredients(client: TestClient) -> None:
    _create_ingredient(client, name="Flour")
    _create_ingredient(client, name="Tomatoes")

    response = client.get("/ingredients")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert names == ["Flour", "Tomatoes"]


def test_get_ingredient(client: TestClient) -> None:
    created = _create_ingredient(client)

    response = client.get(f"/ingredients/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_ingredient(client: TestClient) -> None:
    created = _create_ingredient(client)

    response = client.patch(f"/ingredients/{created['id']}", json={"min_stock": 20})

    assert response.status_code == 200
    assert response.json()["min_stock"] == "20.000"


def test_archive_hides_from_list_but_not_from_direct_get(client: TestClient) -> None:
    created = _create_ingredient(client)

    archive_response = client.delete(f"/ingredients/{created['id']}")
    assert archive_response.status_code == 204

    list_response = client.get("/ingredients")
    assert list_response.json() == []

    get_response = client.get(f"/ingredients/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["archived_at"] is not None


def test_duplicate_name_is_conflict(client: TestClient) -> None:
    _create_ingredient(client, name="Flour")

    response = client.post("/ingredients", json={"name": "Flour", "unit": "kg", "min_stock": 1})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_rename_to_existing_name_is_conflict(client: TestClient) -> None:
    _create_ingredient(client, name="Flour")
    other = _create_ingredient(client, name="Sugar")

    response = client.patch(f"/ingredients/{other['id']}", json={"name": "Flour"})

    assert response.status_code == 409
    assert "Flour" in response.json()["error"]["message"]


def test_bad_unit_is_invalid(client: TestClient) -> None:
    response = client.post("/ingredients", json={"name": "X", "unit": "grams", "min_stock": 1})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_negative_min_stock_is_invalid(client: TestClient) -> None:
    response = client.post("/ingredients", json={"name": "X", "unit": "kg", "min_stock": -1})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_other_restaurant_cannot_read_update_or_archive(
    client: TestClient, other_restaurant: Restaurant, db_session: Session
) -> None:
    other_ingredient = Ingredient(
        restaurant_id=other_restaurant.id, name="Secret", unit="kg", min_stock=Decimal("0")
    )
    db_session.add(other_ingredient)
    db_session.commit()
    db_session.refresh(other_ingredient)

    get_response = client.get(f"/ingredients/{other_ingredient.id}")
    assert get_response.status_code == 404

    patch_response = client.patch(f"/ingredients/{other_ingredient.id}", json={"min_stock": 1})
    assert patch_response.status_code == 404

    delete_response = client.delete(f"/ingredients/{other_ingredient.id}")
    assert delete_response.status_code == 404
