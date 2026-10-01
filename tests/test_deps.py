import pytest

from app.config import settings
from app.deps import get_current_restaurant_id


def test_raises_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")

    with pytest.raises(RuntimeError):
        get_current_restaurant_id()


def test_returns_dev_restaurant_id_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "dev_restaurant_id", 42)

    assert get_current_restaurant_id() == 42


def test_raises_when_dev_restaurant_id_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "dev_restaurant_id", None)

    with pytest.raises(RuntimeError):
        get_current_restaurant_id()
