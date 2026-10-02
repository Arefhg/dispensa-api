import json
import logging
import sys
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logging_config import JsonFormatter
from app.main import app
from app.middleware import RequestIdMiddleware


def _make_record(
    *, level: int = logging.INFO, msg: str = "hello", exc_info: object = None
) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=exc_info,  # type: ignore[arg-type]
    )


def test_json_formatter_without_exception() -> None:
    record = _make_record()

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["logger"] == "test.logger"
    assert "time" in payload
    assert "request_id" in payload
    assert "exc_info" not in payload


def test_json_formatter_with_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        exc_info = sys.exc_info()

    record = _make_record(level=logging.ERROR, msg="failed", exc_info=exc_info)

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert "exc_info" in payload
    assert "ValueError" in payload["exc_info"]
    assert "boom" in payload["exc_info"]


def test_response_has_request_id_header() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    uuid.UUID(request_id)


def test_valid_incoming_request_id_is_reused() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/health", headers={"X-Request-ID": "my-custom-id-123"})

    assert response.headers["X-Request-ID"] == "my-custom-id-123"


def test_invalid_incoming_request_id_is_replaced() -> None:
    bad_id = "not valid! way too long " * 5

    with TestClient(app) as test_client:
        response = test_client.get("/health", headers={"X-Request-ID": bad_id})

    request_id = response.headers["X-Request-ID"]
    assert request_id != bad_id
    uuid.UUID(request_id)


def test_logs_exactly_one_access_line_with_expected_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with TestClient(app) as test_client, caplog.at_level(logging.INFO, logger="app.access"):
        response = test_client.get("/health")

    records = [r for r in caplog.records if r.name == "app.access"]
    assert len(records) == 1

    record = records[0]
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/health"  # type: ignore[attr-defined]
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert record.duration_ms >= 0  # type: ignore[attr-defined]
    assert record.request_id == response.headers["X-Request-ID"]  # type: ignore[attr-defined]


def test_unhandled_exception_logs_error_with_request_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    debug_app = FastAPI()
    debug_app.add_middleware(RequestIdMiddleware)

    @debug_app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    with (
        TestClient(debug_app, raise_server_exceptions=False) as test_client,
        caplog.at_level(logging.INFO, logger="app.access"),
    ):
        # On a crash the 500 response is built outside our middleware, so it
        # never gets an X-Request-ID header -- send one to compare against
        # instead of reading it from the response.
        response = test_client.get("/boom", headers={"X-Request-ID": "crash-test-id"})

    assert response.status_code == 500

    error_records = [r for r in caplog.records if r.name == "app.access" and r.levelname == "ERROR"]
    assert len(error_records) == 1
    assert error_records[0].request_id == "crash-test-id"  # type: ignore[attr-defined]
