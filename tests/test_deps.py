import pytest

from app.config import settings
from app.deps import get_current_restaurant_id


def test_raises_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")

    with pytest.raises(RuntimeError):
        get_current_restaurant_id()
