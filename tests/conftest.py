"""Test-database setup and fixtures.

Big picture:
1. Once per test session: make sure `dispensa_test` exists, then run the real
   `alembic upgrade head` against it -- a broken migration should fail tests,
   not just get silently skipped.
2. Per test: open one connection, start a transaction, hand a Session bound
   to it to both the test and the app (via a get_db override). Whatever the
   app commits only ends a SAVEPOINT inside that transaction. At teardown we
   roll the whole thing back, so no test can leave data for the next one.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_restaurant_id
from app.main import app
from app.models import Restaurant

load_dotenv()
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_test_database_exists() -> None:
    url = make_url(TEST_DATABASE_URL)
    db_name = url.database
    admin_url = url.set(database="postgres")

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
            ).first()
            if exists is None:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


def _run_migrations() -> None:
    os.environ["DATABASE_URL_OVERRIDE"] = TEST_DATABASE_URL
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _test_database_ready() -> None:
    _ensure_test_database_exists()
    _run_migrations()


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def _make_restaurant(db_session: Session, name: str) -> Restaurant:
    restaurant = Restaurant(name=name, address="Test Address", timezone="Europe/Rome")
    db_session.add(restaurant)
    db_session.commit()
    db_session.refresh(restaurant)
    return restaurant


@pytest.fixture
def restaurant(db_session: Session) -> Restaurant:
    return _make_restaurant(db_session, "Test Restaurant A")


@pytest.fixture
def other_restaurant(db_session: Session) -> Restaurant:
    return _make_restaurant(db_session, "Test Restaurant B")


@pytest.fixture
def client(db_session: Session, restaurant: Restaurant) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_current_restaurant_id() -> int:
        return restaurant.id

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_restaurant_id] = override_get_current_restaurant_id

    yield TestClient(app)

    app.dependency_overrides.clear()
